# -*- coding: utf-8 -*-
import requests
from ipaddress import ip_address

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
        response = requests.post(self._bob_api_url + '/start_reconciliation')
        if response.status_code != 200:
            abort(400, 'Bob failed to start reconciliation')
        self._eve_bits_count = 0

    def end_reconciliation(self):
        response = requests.post(self._bob_api_url + '/end_reconciliation')
        if response.status_code != 200:
            abort(400, 'Bob failed to end reconciliation')

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

        response = requests.post(self._bob_api_url + '/ask_parities', json={'blocks': blocks_for_api})
        if response.status_code != 200:
            abort(400, f'error getting parities from Bob: {response.text}')
        parities = response.json()['parities']
        return parities

    def get_eve_bits_count(self):
        return self._eve_bits_count


@app.route('/alice/api/v1.0/reconcile', methods=['POST'])
def reconcile():
    key = get_key_from_request()

    if 'bob_ip' not in request.json:
        abort(400, 'there is no bob_ip parameter in the request')
    bob_ip = ip_address(request.json['bob_ip'])

    if 'qber' not in request.json:
        abort(400, 'there is no qber parameter in the request')
    qber = float(request.json['qber'])

    response = requests.get(f'http://{bob_ip}:{FLASK_PORT_BOB}/bob/api/v1.0/key')
    if response.status_code != 200:
        abort(500, f'Bob is failed to return original key: {response.text}')
    bob_key = response.json()['key']

    channel = RestChannel(f'http://{bob_ip}:{FLASK_PORT_BOB}/bob/api/v1.0')
    reconciliation = Reconciliation('original', channel, key, qber)
    log.info('starting reconciliation')
    reconciliation.reconcile()
    log.info('reconciliation finished')
    reconciled_key = reconciliation.get_reconciled_key()

    if str(reconciled_key) != bob_key:
        log.warning('key is not fully reconciled')
    else:
        log.info('keys are identical')

    return jsonify({
        'reconciled_key': str(reconciled_key),
        'eve_bits_count': channel.get_eve_bits_count()
    })


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT_ALICE, debug=False)
