# -*- coding: utf-8 -*-
from types import SimpleNamespace

# local imports
from common import *

state = SimpleNamespace()


@app.route('/bob/api/v1.0/key', methods=['GET'])
def get_key():
    if not hasattr(state, 'key'):
        abort(404)
    return jsonify({'key': str(state.key)})


@app.route('/bob/api/v1.0/key', methods=['PUT'])
def put_key():
    state.key = get_key_from_request()

    return jsonify({'result': 'key updated'})


if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=True)
