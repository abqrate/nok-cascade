# -*- coding: utf-8 -*-

# local imports
from common import *
from cascade.classical_channel import ClassicalChannel
from cascade.reconciliation import Reconciliation


class RestChannel(ClassicalChannel):
    """
    A concrete implementation of the ClassicalChannel base class.
    """

    def __init__(self, bob_api_url):
        self._bob_api_url = bob_api_url
        self._eve_bits_count = None

    def start_reconciliation(self):
        post_with_retries(self._bob_api_url + '/start_reconciliation', func_descr='Start reconciliation')
        self._eve_bits_count = 0

    def end_reconciliation(self):
        post_with_retries(self._bob_api_url + '/end_reconciliation', func_descr='End reconciliation')

    def ask_parities(self, blocks):
        self._eve_bits_count += len(blocks)
        blocks_for_api = []
        for block in blocks:
            block_for_api = []
            shuffle = block.get_shuffle()
            start_index = block.get_start_index()
            end_index = block.get_end_index()
            for i in range(start_index, end_index):
                block_for_api.append(shuffle.get_key_index(i))
            blocks_for_api.append(block_for_api)

        response_json = post_with_retries(
            self._bob_api_url + '/ask_parities',
            json={'blocks': blocks_for_api},
            func_descr='Ask parities'
        )
        parities = response_json['parities']
        return parities

    def get_eve_bits_count(self):
        return self._eve_bits_count


def consume_rawkey_files():
    normalize_filenames(KEYS_FOLDER_ALICE, 'AliceKey')
    post_with_retries(BOB_API_URL + '/normalize_filenames', func_descr='Consume rawkey files')

    file_paths = {os.path.basename(x): x for x in glob.glob(os.path.join(KEYS_FOLDER_ALICE, f'20*.dat'))}
    for filename in sorted(file_paths.keys()):
        file_path = file_paths[filename]
        with open(file_path, 'rb') as f:
            rawkey = f.read()
        _result_json = post_with_retries(
            BOB_API_URL + '/consume_rawkey_file',
            json={'filename': filename, 'size': len(rawkey)},
            func_descr='Consume rawkey files'
        )
        if _result_json['result'] != 'ok':
            log.warning('failed to read rawkey file on the Bob side, skipping')
        else:
            state.rawkey_buffer += rawkey

        os.remove(file_path)
        if len(state.rawkey_buffer) >= KEYFRAME_SIZE:
            break


def estimate_qber() -> float:
    _result_json = post_with_retries(BOB_API_URL + '/split_off_keypart_for_qber_estimation', func_descr='Estimate QBER')
    keypart_bob = bitarray(_result_json['keypart'])
    keypart_alice = split_off_keypart_for_qber_estimation()
    assert len(keypart_alice) == len(keypart_bob)
    diff_count = len([i for i in range(0, len(keypart_bob)) if keypart_alice[i] != keypart_bob[i]])
    _qber_estimated = 1.0 * diff_count / len(keypart_alice)
    if _qber_estimated < 0.01:
        _qber_estimated = 0.01
    return _qber_estimated


def reconcile_frame(qber: float) -> int:
    channel = RestChannel(BOB_API_URL)
    reconciliation = Reconciliation('original', channel, state.key, qber)
    log.info('starting reconciliation')
    reconciliation.reconcile()
    log.info('reconciliation finished')
    state.key = reconciliation.get_reconciled_key()
    return channel.get_eve_bits_count()


def security_amplification(bits_compromised: int):
    post_with_retries(
        BOB_API_URL + '/calc_security_amplified_key',
        json={'bits_compromised': bits_compromised},
        func_descr='Security amplification'
    )
    calc_security_amplified_key(bits_compromised)


def write_keys():
    filename = f'{datetime.datetime.now():%Y%m%d-%H%M%S-%f.dat}'
    post_with_retries(BOB_API_URL + '/write_amp_key', json={'filename': filename}, func_descr='Write keys')
    write_amp_key(KEYS_FOLDER_ALICE, filename)


if __name__ == '__main__':
    post_with_retries(BOB_API_URL + '/reset_state', func_descr='Alice main cycle')
    reset_state()

    while True:
        if len(state.rawkey_buffer) < KEYFRAME_SIZE:
            log.info('consuming some input raw key files')
            consume_rawkey_files()

        if len(state.rawkey_buffer) < KEYFRAME_SIZE:
            log.info('not enough raw key, waiting for new rawkey files...')
            while len(state.rawkey_buffer) < KEYFRAME_SIZE:
                sleep(DELAY_ON_WAITING_RAWKEY_FILES)
                consume_rawkey_files()

        post_with_retries(BOB_API_URL + '/split_off_keyframe', 'Alice main cycle')
        split_off_keyframe()

        qber_estimated = estimate_qber()
        if qber_estimated > MAX_ESTIMATED_QBER:
            log.info(f'estimated QBER is too big - {qber_estimated*100:.1f}%, skipping this frame')
            continue

        eve_bits_count = reconcile_frame(qber_estimated)

        result_json = post_with_retries(BOB_API_URL + '/calc_hash_for_compare', func_descr='Alice main cycle')
        bob_hash = bitarray(result_json['hash'])
        alice_hash = calc_hash_for_compare()
        if alice_hash != bob_hash:
            log.info('reconciliation failed (keys are different), skipping this frame')
            continue

        total_bits_compromised = eve_bits_count + COMPARE_FRAME_TOEPLITZ_HEIGHT
        if total_bits_compromised >= state.key.get_size():
            log.info(f'security amplification is not possible, Eve got too many bits: {total_bits_compromised}')
            continue

        security_amplification(total_bits_compromised)

        write_keys()
