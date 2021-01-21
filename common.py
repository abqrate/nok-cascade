# -*- coding: utf-8 -*-
import logging
from flask import Flask, jsonify, make_response, request, abort

# local imports
from cascade.key import Key

FLASK_HOST = '0.0.0.0'
FLASK_PORT = 15994

# configure logging
logging.basicConfig(format='%(levelname)-8s [%(asctime)s] %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

app = Flask(__name__)


def get_key_from_request() -> Key:
    if not request.json or 'key' not in request.json:
        abort(400)

    key_str = request.json['key']
    try:
        return Key(key_str)
    except ValueError:
        abort(400)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': str(error)}), 404)


@app.errorhandler(400)
def bad_request_400(error):
    return make_response(jsonify({'error': str(error)}), 400)


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
