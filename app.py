import logging
import os
import re

import yaml
from flask import Flask, request
from slack_sdk import WebClient
from werkzeug.exceptions import BadRequest

from cache import get_from_cache, set_in_cache
from game import get_deviation, get_rank, get_rating, process_result

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.config.from_file(os.path.join('settings', 'base.yml'), yaml.safe_load)
app.config.from_file(
    os.path.join('settings', os.environ.get('PONG_DEPLOYMENT_MODE', 'local') + '.yml'),
    yaml.safe_load
)


def send_to_slack(text):
    client = WebClient(token=app.config['SLACK']['BOT_TOKEN'])
    client.chat_postMessage(channel='#fun-dublin-pingpong', text=text)


def get_name_from_user_id(user_id):
    client = WebClient(token=app.config['SLACK']['BOT_TOKEN'])
    return client.users_info(user=user_id)['user']['profile']['display_name']


def handle_result(body, regex_match):
    p1, _, p2 = regex_match[0].split()
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
    p1_rating = get_rating(p1_id)
    p2_rating = get_rating(p2_id)
    send_to_slack('{}: {}'.format(get_name_from_user_id(p1_id), p1_rating))
    send_to_slack('{}: {}'.format(get_name_from_user_id(p2_id), p2_rating))


def handle_rank():
    text = "\n"
    for player_id, rank in get_rank():
        text += "{}: {}\n".format(get_name_from_user_id(player_id), rank)
    send_to_slack(text)


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
    if body['type'] != 'event_callback':
        return {}
    app.logger.info(body['event']['text'])
    result_pattern = re.compile('<@[A-Z0-9]+>\s+beat\s+<@[A-Z0-9]+>')
    matches = result_pattern.findall(body['event']['text'])
    if matches:
        handle_result(body, matches)
        return {}
    rank_pattern = re.compile('\s+rank\s*')
    matches = rank_pattern.findall(body['event']['text'])
    if matches:
        handle_rank()
        return {}
    send_to_slack("I didn't understand that...")
    return {}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

