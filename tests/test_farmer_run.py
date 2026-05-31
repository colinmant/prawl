import time
import pytest
from unittest.mock import MagicMock
from core.farmer import Farmer


def make_running_farmer(match_time=25, multiplier=1, max_games_amount=1):
    """Build a Farmer wired up so _run() completes instantly in timer mode."""
    keybinds = {k: 'x' for k in ('key_up', 'key_left', 'key_down', 'key_right',
                                   'key_light', 'key_heavy', 'key_throw')}
    settings = {
        **keybinds,
        'network_mode': False,
        'match_time': match_time,
        'exp_multiplier': multiplier,
        'timer_sound': False,
        'early_dc_thresh': 50,
        'rate_limit_detect': False,
        'max_games': True,
        'max_games_amount': max_games_amount,
    }

    interface = MagicMock()
    interface.get.side_effect = settings.get

    process = MagicMock()
    process.get_hwnd.return_value = 12345

    farmer = Farmer(
        process=process,
        interface=interface,
        keyseq=MagicMock(),
        network=None,
    )
    farmer.on_stop_callback = None
    return farmer


def run_and_join(farmer, timeout=5):
    """Start the farmer with minutes=0 (match ends immediately) and wait for thread."""
    farmer.start(minutes=0, sequence=[])
    thread = farmer._timer_thread  # may already be None if thread finished before this line
    if thread is not None:
        thread.join(timeout=timeout)
        assert not thread.is_alive(), "farmer thread did not finish within timeout"
    else:
        # thread finished so fast stop() already nulled it — poll until running=False
        deadline = time.time() + timeout
        while farmer.running and time.time() < deadline:
            time.sleep(0.001)
    assert not farmer.running, "farmer did not stop within timeout"


# --- full-loop XP tests ---

def test_one_match_gains_correct_xp():
    farmer = make_running_farmer(match_time=25, multiplier=1, max_games_amount=1)
    run_and_join(farmer)
    assert farmer.total_exp == 1000

def test_one_match_gains_correct_gold():
    farmer = make_running_farmer(match_time=25, multiplier=1, max_games_amount=1)
    run_and_join(farmer)
    assert farmer.total_gold == 250

def test_three_matches_accumulate_xp():
    farmer = make_running_farmer(match_time=25, multiplier=1, max_games_amount=3)
    run_and_join(farmer)
    assert farmer.total_exp == 3000
    assert farmer.total_games == 3

def test_multiplier_applied_over_run():
    farmer = make_running_farmer(match_time=25, multiplier=2, max_games_amount=2)
    run_and_join(farmer)
    assert farmer.total_exp == 4000

def test_farmer_stops_after_max_games():
    farmer = make_running_farmer(max_games_amount=2)
    run_and_join(farmer)
    assert farmer.total_games == 2
    assert farmer.running is False

def test_farmer_not_running_after_completion():
    farmer = make_running_farmer(max_games_amount=1)
    run_and_join(farmer)
    assert farmer.running is False
