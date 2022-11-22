import math
from datetime import datetime

from cache import get_from_cache, set_in_cache

Q = 0.00575646273


def get_rating(player_id):
    return get_from_cache('rating:{}'.format(player_id))


def get_deviation(player_id):
    return get_from_cache('deviation:{}'.format(player_id))


def get_rank():
    all_player_id_str = get_from_cache('players')
    unranked = []
    for player_id in all_player_id_str.split(','):
        rating = get_rating(player_id)
        if rating:
            unranked.append((player_id, int(rating)))
    return sorted(unranked, key=lambda x: x[1], reverse=True)


def get_stats(player_id):
    rating, rating_lock = get_from_cache('rating:{}'.format(player_id), True)
    deviation, deviation_lock = get_from_cache('deviation:{}'.format(player_id), True)
    time, time_lock = get_from_cache('time:{}'.format(player_id), True)
    return (int(rating) if rating else 1500, rating_lock), (int(deviation) if deviation else 350, deviation_lock), (int(time) if time else None, time_lock)


def set_stats(player_id, rating, rating_lock, deviation, deviation_lock, time, time_lock):
    set_in_cache('rating:{}'.format(player_id), rating, rating_lock)
    set_in_cache('deviation:{}'.format(player_id), deviation, deviation_lock)
    set_in_cache('time:{}'.format(player_id), time, time_lock)


def update_deviation_time_uncertainty(deviation, periods):
    return min(int(math.sqrt(deviation**2 + 35**2 * periods)), 350)


def g(deviation):
    return 1 / math.sqrt(1 + 3 * Q**2 * deviation**2 / math.pi**2)


def expectation(player_rating, opponent_rating, opponent_deviation):
    e = g(opponent_deviation) * (player_rating - opponent_rating) / -400
    return 1 / (1 + 10**e)


def inverse_d_squared(player_rating, opponent_rating, opponent_deviation):
    exp = expectation(player_rating, opponent_rating, opponent_deviation)
    return Q**2 * g(opponent_deviation)**2 * exp * (1 - exp)


def update_rating(player_rating, player_deviation, opponent_rating, opponent_deviation, score):
    ids = inverse_d_squared(player_rating, opponent_rating, opponent_deviation)
    exp = expectation(player_rating, opponent_rating, opponent_deviation)
    return int(player_rating + Q / (1 / player_deviation**2 + ids) * g(opponent_deviation) * (score - exp))


def update_deviation(player_rating, player_deviation, opponent_rating, opponent_deviation):
    ids = inverse_d_squared(player_rating, opponent_rating, opponent_deviation)
    return int(1 / math.sqrt(1 / player_deviation**2 + ids))


def get_num_rating_periods(result_time, previous_time):
    HALF_WEEK_IN_SECONDS = 60 * 60 * 24 * 3.5
    return (datetime.fromtimestamp(result_time) - datetime.fromtimestamp(previous_time)).total_seconds() / HALF_WEEK_IN_SECONDS


def process_result(winner_id, loser_id, result_time):
    (winner_rating, winner_rating_lock), (winner_deviation, winner_deviation_lock), (winner_time, winner_time_lock) = get_stats(winner_id)
    (loser_rating, loser_rating_lock), (loser_deviation, loser_deviation_lock), (loser_time, loser_time_lock) = get_stats(loser_id)
    timed_winner_deviation, timed_loser_deviation = winner_deviation, loser_deviation
    if winner_time:
        timed_winner_deviation = update_deviation_time_uncertainty(winner_deviation, get_num_rating_periods(result_time, winner_time))
    if loser_time:
        timed_loser_deviation = update_deviation_time_uncertainty(loser_deviation, get_num_rating_periods(result_time, loser_time))
    new_winner_rating = update_rating(winner_rating, timed_winner_deviation, loser_rating, timed_loser_deviation, 1)
    new_loser_rating = update_rating(loser_rating, timed_loser_deviation, winner_rating, timed_winner_deviation, 0)
    new_winner_deviation = update_deviation(new_winner_rating, timed_winner_deviation, loser_rating, timed_loser_deviation)
    new_loser_deviation = update_deviation(new_loser_rating, timed_loser_deviation, winner_rating, timed_winner_deviation)
    set_stats(winner_id, new_winner_rating, winner_rating_lock, new_winner_deviation, winner_deviation_lock, result_time, winner_time_lock)
    set_stats(loser_id, new_loser_rating, loser_rating_lock, new_loser_deviation, loser_deviation_lock, result_time, loser_time_lock)

