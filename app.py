import logging
import os
import re

import yaml
from flask import Flask, request
from werkzeug.exceptions import BadRequest

from cache import get_from_cache, set_in_cache
from game import process_result

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
    if body['type'] == 'url_verification':
        return {'challenge': body['challenge']}
    if body['type'] == 'event_callback':
        pattern = re.compile('<@[A-Z0-9]+>\s+beat\s+<@[A-Z0-9]+>')
        matches = pattern.findall(body['event']['text'])
        if not matches:
            return {}
        p1, _, p2 = matches[0].split()
        player_pattern = re.compile('<@([A-Z0-9]+)>')
        p1_id = player_pattern.match(p1).groups()[0]
        p2_id = player_pattern.match(p2).groups()[0]
        current_players_str, lock = get_from_cache('players', True)
        current_players = set(current_players_str.split(',')) if current_players_str else set()
        current_players.add(p1_id)
        current_players.add(p2_id)
        current_players_str = ','.join(current_players)
        set_in_cache('players', current_players_str, lock)
        process_result(p1_id, p2_id, body['event_time'])
    return {}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

