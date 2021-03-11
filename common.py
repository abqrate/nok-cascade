# -*- coding: utf-8 -*-
import logging
import glob
import os
import datetime
import requests
import numpy as np
from time import sleep
from types import SimpleNamespace
from bitarray import bitarray
from scipy.linalg import toeplitz
from math import ceil


# local imports
from config import *
from cascade.key import Key

BOB_API_URL = f'http://{BOB_IP}:{FLASK_PORT}/bob/api/v1.0'
DELAY_ON_WAITING_RAWKEY_FILES = 1.0  # delay before checking key's directory for new files, in seconds

# configure logging
logging.basicConfig(format='%(levelname)-8s [%(asctime)s] %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


state = SimpleNamespace()
state.random_seed = b''                  # random bytes for Toeplitz matrix construction
state.toeplitz_cmp = toeplitz([])        # Toeplitz matrix for key comparison
state.toeplitz_amp = toeplitz([])        # Toeplitz matrix for security amplification
state.rawkey_buffer = bytearray()        # here are input raw key files read
state.key = Key()                        # current key to be reconciled
state.amp_key = bitarray()               # key after security amplification applied
state.reconciliation_started = False     # flag, used on Bob only


def reset_state():
    # reading random seed
    with open(RANDOM_SEED_FILENAME, 'rb') as f:
        state.random_seed = f.read()

    # calculating keyframe size after QBER estimation
    frame_size = KEYFRAME_SIZE*8  # keyframe size in bits
    small_part_size = int(frame_size*KEYPART_QBER_ESTIMATION/KEYPART_QBER_ESTIMATION_SPLITS)
    frame_size = frame_size - small_part_size*KEYPART_QBER_ESTIMATION_SPLITS
    assert frame_size > 0

    # calculating number of bytes needed for Toeplitz matrices construction
    random_bytes_needed = ceil((COMPARE_FRAME_TOEPLITZ_HEIGHT + frame_size*3) / 8.0)
    assert len(state.random_seed) >= random_bytes_needed

    # split off needed bytes and convert them to array of bits
    random_bits = bitarray()
    random_bits.frombytes(bytes(state.random_seed[:random_bytes_needed]))
    state.random_seed = state.random_seed[random_bytes_needed:]

    # constructing Toeplitz matrix for reconciled keys comparison
    column = [int(x) for x in random_bits[:COMPARE_FRAME_TOEPLITZ_HEIGHT]]
    random_bits = random_bits[COMPARE_FRAME_TOEPLITZ_HEIGHT:]
    row = [int(x) for x in random_bits[:frame_size]]
    random_bits = random_bits[frame_size:]
    state.toeplitz_cmp = toeplitz(column, row)

    # constructing Toeplitz matrix for security amplification
    column = [int(x) for x in random_bits[:frame_size-COMPARE_FRAME_TOEPLITZ_HEIGHT]]
    random_bits = random_bits[COMPARE_FRAME_TOEPLITZ_HEIGHT-COMPARE_FRAME_TOEPLITZ_HEIGHT:]
    row = [int(x) for x in random_bits[:frame_size]]
    # random_bits = random_bits[frame_size:]
    state.toeplitz_amp = toeplitz(column, row)

    state.rawkey_buffer = bytearray()
    state.key = Key()
    state.amp_key = bitarray()
    state.reconciliation_started = False


def split_off_keypart_for_qber_estimation() -> bitarray:
    str_key = str(state.key)
    assert len(str_key) == KEYFRAME_SIZE*8
    small_part_size = int(KEYFRAME_SIZE*8 * KEYPART_QBER_ESTIMATION / KEYPART_QBER_ESTIMATION_SPLITS)
    small_parts_distance = int(KEYFRAME_SIZE*8 / KEYPART_QBER_ESTIMATION_SPLITS)
    str_keypart = ''

    offset = 0
    for _ in range(0, KEYPART_QBER_ESTIMATION_SPLITS):
        str_keypart += str_key[offset:offset+small_part_size]
        str_key = str_key[:offset] + str_key[offset+small_part_size:]
        offset += small_parts_distance-small_part_size

    state.key = Key(str_key)

    return bitarray(str_keypart)


def calc_security_amplified_key(bits_compromised: int):
    assert bits_compromised < state.key.get_size()
    assert bits_compromised >= COMPARE_FRAME_TOEPLITZ_HEIGHT
    key_vector = [ord(x)-ord('0') for x in str(state.key)]
    amp_vector = np.dot(state.toeplitz_amp, key_vector)
    amp_vector = amp_vector[:state.key.get_size() - bits_compromised]
    state.amp_key = bitarray(amp_vector)


def normalize_filenames(folder: str, prefix: str):
    for filepath in glob.glob(os.path.join(folder, f'{prefix}*.dat')):
        filename = os.path.basename(filepath)
        try:
            dt = datetime.datetime.strptime(filename, f'{prefix}%d-%m-%Y_%H-%M-%S.dat')
            os.rename(filepath, os.path.join(folder, f'{dt:%Y%m%d-%H%M%S.dat}'))
        except ValueError:
            log.error(f'incorrect filename format: {filename}, renaming and ignoring')
            os.rename(filepath, filepath[:-3] + 'bad')


def post_with_retries(url: str, func_descr, json: object = None):
    response = requests.post(url, json=json)

    try_num = 1
    while response.status_code != 200:
        if try_num == HTTP_RETRIES_BEFORE_FAILURE:
            raise RuntimeError(f'{func_descr}: http request failed after too many tries: {response.text}')
        log.warning(f'{func_descr}: http request error: {response.text.strip()}, retrying after delay...')
        sleep(HTTP_RETRIES_DELAY_ON_ERROR)
        response = requests.post(url, json=json)

    return response.json()


def split_off_keyframe():
    assert len(state.rawkey_buffer) >= KEYFRAME_SIZE
    b = bitarray()
    b.frombytes(bytes(state.rawkey_buffer[:KEYFRAME_SIZE]))
    state.rawkey_buffer = state.rawkey_buffer[KEYFRAME_SIZE:]
    state.key = Key(b.to01())


def calc_hash_for_compare() -> bitarray:
    assert state.key.get_size() == len(state.toeplitz_cmp)

    key_vector = [ord(c)-ord('0') for c in str(state.key)]
    result = np.dot(state.toeplitz_compare, key_vector)

    return bitarray(result)


def write_amp_key(folder, filename):
    assert len(state.amp_key) > 0
    amp_key_size = len(state.amp_key) // 8 * 8
    key_bytes = state.amp_key[:amp_key_size].tobytes()
    file_path = os.path.join(folder, filename)
    with open(file_path, 'wb') as f:
        f.write(key_bytes)
    state.amp_key = bitarray()
