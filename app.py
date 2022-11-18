import logging
import os

import yaml
from flask import Flask, request
from werkzeug.exceptions import BadRequest

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.config.from_file(
    os.path.join('settings', os.environ.get('PONG_DEPLOYMENT_MODE', 'local') + '.yml'),
    yaml.safe_load
)


@app.route('/', methods=['GET', 'POST'])
def index(**kwargs):
    try:
        body = request.get_json()
    except BadRequest:
        return {}
    if 'type' not in body:
        return {}
    app.logger.info(body['type'])
    if body['type'] == 'url_verification':
        return {'challenge': body['challenge']}
    return {}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

