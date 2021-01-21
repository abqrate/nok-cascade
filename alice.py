# -*- coding: utf-8 -*-
from ipaddress import ip_address
from types import SimpleNamespace

# local imports
from common import *

state = SimpleNamespace()


@app.route('/alice/api/v1.0/reconcile', methods=['POST'])
def reconcile():
    state.key = get_key_from_request()

    if 'bob_ip' not in request.json:
        abort(400)
    state.bob_ip = ip_address(request.json['bob_ip'])

    return jsonify({'result': 'ok'})


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)
