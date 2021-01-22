# -*- coding: utf-8 -*-
from types import SimpleNamespace

# local imports
from common import *

state = SimpleNamespace()
state.key = None
state.reconciliation_started = False


@app.route('/bob/api/v1.0/key', methods=['GET'])
def get_key():
    if state.key is None:
        abort(400, 'get_key: key is undefined')

    return jsonify({'key': str(state.key)})


@app.route('/bob/api/v1.0/key', methods=['PUT'])
def put_key():
    if state.reconciliation_started:
        log.warning('put_key: reconciliation is in progress')

    state.key = get_key_from_request()
    state.reconciliation_started = False

    return jsonify({'result': 'key updated'})


@app.route('/bob/api/v1.0/start_reconciliation', methods=['POST'])
def start_reconciliation():
    if state.key is None:
        abort(400, 'start_reconciliation: key is undefined')

    if state.reconciliation_started:
        log.warning('start_reconciliation: reconciliation is already in progress')

    state.reconciliation_started = True

    return jsonify({'result': 'ok'})


@app.route('/bob/api/v1.0/end_reconciliation', methods=['POST'])
def end_reconciliation():
    if state.key is None:
        log.warning('end_reconciliation: key is undefined')

    if not state.reconciliation_started:
        log.warning('end_reconciliation: reconciliation is not in progress')

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


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT_BOB, debug=False)
