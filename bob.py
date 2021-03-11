# -*- coding: utf-8 -*-
from flask import Flask, jsonify, make_response, request, abort

# local imports
from common import *

app = Flask(__name__)


@app.route('/bob/api/v1.0/reset_state', methods=['POST'])
def reset_state_on_bob():
    reset_state()
    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/split_off_keyframe', methods=['POST'])
def split_off_keyframe_on_bob():
    split_off_keyframe()
    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/normalize_filenames', methods=['POST'])
def normalize_filenames_on_bob():
    normalize_filenames(KEYS_FOLDER_BOB, 'BobKey')
    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/consume_rawkey_file', methods=['POST'])
def consume_rawkey_file_on_bob():
    if not request.json or 'filename' not in request.json:
        abort(400, 'there is no "filename" parameter in the request')

    filename_to_read = request.json['filename']
    if not isinstance(filename_to_read, str):
        abort(400, '"filename" parameter must be string')

    if not request.json or 'size' not in request.json:
        abort(400, 'there is no "size" parameter in the request')

    size = request.json['size']
    if not isinstance(size, int):
        abort(400, '"size" parameter must be string')

    file_paths = {os.path.basename(x): x for x in glob.glob(os.path.join(KEYS_FOLDER_BOB, f'20*.dat'))}
    for filename in sorted(file_paths.keys()):
        file_path = file_paths[filename]
        if filename >= filename_to_read:
            break
        log.warning(f'deleting orphan rawkey file {filename}')
        os.remove(file_path)

    if filename_to_read not in file_paths:
        log.warning(f'rawkey file {filename_to_read} does not exists')
        return jsonify({'result': 'failed', 'details': 'file not found'})

    file_path = file_paths[filename_to_read]
    with open(file_path, 'rb') as f:
        rawkey = f.read()
    os.remove(file_path)

    if len(rawkey) != size:
        log.warning(f'rawkey file {filename_to_read} has incorrect size: {len(rawkey)}, skipping')
        return jsonify({'result': 'failed', 'details': 'file has incorrect size: {len(rawkey)}'})

    state.rawkey_buffer += rawkey
    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/write_amp_key', methods=['POST'])
def write_amp_key_on_bob():
    if not request.json or 'filename' not in request.json:
        abort(400, 'there is no "filename" parameter in the request')

    filename = request.json['filename']
    if not isinstance(filename, str):
        abort(400, '"filename" parameter must be string')

    write_amp_key(KEYS_FOLDER_BOB, filename)
    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/split_off_keypart_for_qber_estimation', methods=['POST'])
def split_off_keypart_for_qber_estimation_on_bob():
    keypart = split_off_keypart_for_qber_estimation()
    return jsonify({'result': 'ok', 'keypart': keypart.to01()})


@app.route('/bob/api/v1.0/calc_hash_for_compare', methods=['POST'])
def calc_hash_for_compare_on_bob():
    bob_hash = calc_hash_for_compare()
    return jsonify({'result': 'ok', 'hash': bob_hash.to01()})


@app.route('/bob/api/v1.0/calc_security_amplified_key', methods=['POST'])
def calc_security_amplified_key_on_bob():
    if not request.json or 'bits_compromised' not in request.json:
        abort(400, 'there is no "bits_compromised" parameter in the request')

    bits_compromised = request.json['bits_compromised']
    if not isinstance(bits_compromised, int):
        abort(400, '"bits_compromised" parameter must be integer')

    calc_security_amplified_key(bits_compromised)
    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/start_reconciliation', methods=['POST'])
def start_reconciliation():
    if state.key is None:
        abort(400, 'start_reconciliation: key is undefined')

    if state.reconciliation_started:
        abort(400, 'start_reconciliation: reconciliation is already in progress')

    state.reconciliation_started = True

    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/end_reconciliation', methods=['POST'])
def end_reconciliation():
    if state.key is None:
        abort(400, 'end_reconciliation: key is undefined')

    if not state.reconciliation_started:
        abort(400, 'end_reconciliation: reconciliation is not in progress')

    state.reconciliation_started = False
    state.key = None

    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/ask_parities', methods=['POST'])
def ask_parities():
    if state.key is None:
        abort(400, 'ask_parities: key is undefined')

    if not state.reconciliation_started:
        abort(400, 'ask_parities: reconciliation is not in progress')

    if not request.json or 'blocks' not in request.json:
        abort(400, 'there is no "blocks" parameter in the request')

    blocks = request.json['blocks']
    if not isinstance(blocks, list):
        abort(400, '"blocks" parameter must be list')

    parities = []
    for block in blocks:
        if not isinstance(block, list):
            abort(400, '"blocks" parameter must be list of lists')

        parity = 0
        for key_index in block:
            if not isinstance(key_index, int):
                abort(400, '"blocks" parameter must be list of lists of integers')
            try:
                if state.key.get_bit(key_index):
                    parity = 1 - parity
            except KeyError:
                abort(400, f'key index {key_index} is out of bounds')

        parities.append(parity)

    return jsonify({'parities': parities})


@app.errorhandler(400)
def bad_request_400(error):
    return make_response(jsonify({'error': str(error)}), 400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': str(error)}), 404)


@app.errorhandler(405)
def bad_request_405(error):
    return make_response(jsonify({'error': str(error)}), 405)


@app.errorhandler(500)
def server_error(error):
    return make_response(jsonify({'error': str(error)}), 500)


@app.errorhandler(ValueError)
def value_error(error):
    return make_response(jsonify({'error': str(error)}), 500)


@app.errorhandler(Exception)
def general_exception(error):
    return make_response(jsonify({'error': str(error)}), 500)


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
