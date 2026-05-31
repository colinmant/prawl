import pytest
from unittest.mock import MagicMock
from core._utils import calculate_exp, calculate_gold
from core.farmer import Farmer


# --- calculate_exp unit tests ---

def test_full_match_base_rate():
    assert calculate_exp(25, 1) == 1000

def test_partial_match_base_rate():
    assert calculate_exp(10, 1) == pytest.approx(400)

def test_minutes_capped_at_25():
    assert calculate_exp(30, 1) == calculate_exp(25, 1)

def test_multiplier_doubles_exp():
    assert calculate_exp(25, 2) == 2000

def test_partial_match_with_multiplier():
    assert calculate_exp(10, 2) == pytest.approx(800)

def test_zero_minutes_gives_zero():
    assert calculate_exp(0, 1) == 0


# --- calculate_gold unit tests ---

def test_full_match_gold():
    assert calculate_gold(25, 1) == 250

def test_gold_capped_at_25_minutes():
    assert calculate_gold(99, 1) == calculate_gold(25, 1)


# --- Farmer._match_end integration tests ---

def make_farmer(match_time=25, multiplier=1):
    interface = MagicMock()
    interface.get.side_effect = lambda key: {
        'match_time': match_time,
        'exp_multiplier': multiplier,
        'timer_sound': False,
    }.get(key)

    farmer = Farmer(
        process=MagicMock(),
        interface=interface,
        keyseq=MagicMock(),
        network=MagicMock(),
    )
    farmer.on_stop_callback = None
    return farmer


def test_match_end_increments_total_exp():
    farmer = make_farmer(match_time=25, multiplier=1)
    farmer._match_end()
    assert farmer.total_exp == 1000

def test_match_end_increments_current_exp():
    farmer = make_farmer(match_time=25, multiplier=1)
    farmer._match_end()
    assert farmer.current_exp == 1000

def test_match_end_accumulates_over_multiple_games():
    farmer = make_farmer(match_time=25, multiplier=1)
    farmer._match_end()
    farmer._match_end()
    farmer._match_end()
    assert farmer.total_exp == 3000

def test_match_end_increments_game_count():
    farmer = make_farmer()
    farmer._match_end()
    farmer._match_end()
    assert farmer.total_games == 2

def test_match_end_with_multiplier():
    farmer = make_farmer(match_time=25, multiplier=2)
    farmer._match_end()
    assert farmer.total_exp == 2000


# --- Farmer._limits tests ---

def make_farmer_for_limits(rate_limit_detect=True, rate_limit_wait=False,
                            rate_limit_wait_time=0, max_games=False, max_games_amount=0):
    interface = MagicMock()
    interface.get.side_effect = lambda key: {
        'rate_limit_detect': rate_limit_detect,
        'rate_limit_wait': rate_limit_wait,
        'rate_limit_wait_time': rate_limit_wait_time,
        'max_games': max_games,
        'max_games_amount': max_games_amount,
    }.get(key)

    farmer = Farmer(
        process=MagicMock(),
        interface=interface,
        keyseq=MagicMock(),
        network=MagicMock(),
    )
    farmer.on_stop_callback = None
    farmer.running = True
    return farmer


def test_rate_limit_stops_farmer_at_13000():
    farmer = make_farmer_for_limits(rate_limit_detect=True, rate_limit_wait=False)
    farmer.current_exp = 13000
    result = farmer._limits()
    assert result is True
    assert farmer.running is False

def test_no_rate_limit_below_13000():
    farmer = make_farmer_for_limits(rate_limit_detect=True)
    farmer.current_exp = 12999
    result = farmer._limits()
    assert result is False

def test_rate_limit_disabled_does_not_stop():
    farmer = make_farmer_for_limits(rate_limit_detect=False)
    farmer.current_exp = 99999
    result = farmer._limits()
    assert result is False

def test_max_games_stops_farmer():
    farmer = make_farmer_for_limits(max_games=True, max_games_amount=5)
    farmer.total_games = 5
    result = farmer._limits()
    assert result is True
    assert farmer.running is False

def test_max_games_not_reached_continues():
    farmer = make_farmer_for_limits(max_games=True, max_games_amount=5)
    farmer.total_games = 4
    result = farmer._limits()
    assert result is False
