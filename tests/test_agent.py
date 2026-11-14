"""Tests for submission/agent.py.

The competition SDK is not on the public package index, so this file installs a
tiny stand-in for `poker_agent_sdk` before importing the bot.  The stand-in has
only what the bot uses: an Agent base class and the Action constructors.
"""
import importlib.util
import pathlib
import sys
import time
import types
from types import SimpleNamespace as NS

import pytest


class _Action:
    def __init__(self, kind, amount=None, cards=()):
        self.kind, self.amount, self.cards = kind, amount, cards

    @classmethod
    def raise_to(cls, amount):
        return cls("raise", amount)

    @classmethod
    def check(cls):
        return cls("check")

    @classmethod
    def call(cls):
        return cls("call")

    @classmethod
    def fold(cls):
        return cls("fold")


_sdk = types.ModuleType("poker_agent_sdk")
_sdk.Agent = type("Agent", (), {})
_sdk.Action = _Action
sys.modules.setdefault("poker_agent_sdk", _sdk)

_path = pathlib.Path(__file__).resolve().parents[1] / "submission" / "agent.py"
_spec = importlib.util.spec_from_file_location("agent", _path)
agent = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agent)
agent.DEBUG = True          # let errors surface in tests


class _Raise:
    def __init__(self, lo, hi):
        self.min_amount, self.max_amount = lo, hi


def ev(kind, seat=None, amount=0):
    return {"kind": kind, "seat": seat, "amount": amount}


def make_state(cards, stacks, bets, history, me=0, boards=((), ()), phase="betting",
               bb=20, pot=None, to_call=None, discarded=None, folded=(), events=None):
    """Build a game state shaped like the SDK's, for one decision."""
    curmax = max(bets)
    if to_call is None:
        to_call = min(max(0, curmax - bets[me]), stacks[me])
    legal = {"fold": to_call > 0, "check": to_call == 0, "call": to_call > 0, "raise": None}
    if phase == "betting" and stacks[me] > to_call:
        legal["raise"] = _Raise(min(curmax + bb, bets[me] + stacks[me]), bets[me] + stacks[me])
    seats = [NS(seat=i, stack=stacks[i], bet=bets[i],
                status="folded" if i in folded else "busted" if stacks[i] + bets[i] == 0
                else "all_in" if stacks[i] == 0 else "active") for i in range(len(stacks))]
    return NS(seat=me, seats=seats, cards=tuple(cards), board=tuple(boards[0]),
              variant={"boards": [list(boards[0]), list(boards[1])], "discarded": discarded},
              history=history, events=history if events is None else events,
              blinds=NS(big_blind=bb, small_blind=bb // 2),
              pot=sum(bets) if pot is None else pot, to_call=to_call,
              config=NS(payouts=[50, 30, 20]), time_bank_ms=100, phase=phase,
              can=lambda name: legal.get(name)), legal


def check_legal(action, legal):
    assert legal.get(action.kind), f"illegal action {action.kind}"
    if action.kind == "raise":
        r = legal["raise"]
        assert r.min_amount <= action.amount <= r.max_amount


BLINDS = [ev("blind", 1, 10), ev("blind", 2, 20)]
DEEP = dict(stacks=[2000, 1990, 1980, 2000, 2000, 2000, 2000, 2000], bets=[0, 10, 20, 0, 0, 0, 0, 0])
BOT = agent.Agent()


def test_tables_loaded():
    assert len(agent.HANDS) == 22100            # every 3-card hand
    aces = agent.HANDS[agent.cidx(*sorted(agent.CM[c] for c in ("As", "Ah", "Ad")))]
    junk = agent.HANDS[agent.cidx(*sorted(agent.CM[c] for c in ("7s", "2h", "3d")))]
    assert aces[0] < 0.05 < 0.9 < junk[0]       # column 0 = share of hands that are better


def test_premium_raises_first_in():
    state, legal = make_state(["As", "Ah", "Ks"], me=3, history=BLINDS, **DEEP)
    action, memory = BOT.act(state, b"")
    check_legal(action, legal)
    assert action.kind == "raise"
    assert isinstance(memory, bytes) and len(memory) < 16_000


def test_junk_folds_first_in():
    state, legal = make_state(["7s", "2h", "3d"], me=3, history=BLINDS, **DEEP)
    action, _ = BOT.act(state, b"")
    check_legal(action, legal)
    assert action.kind == "fold"


def test_junk_folds_to_a_shove():
    history = BLINDS + [ev("raise", 3, 2000)]
    state, legal = make_state(["7s", "2h", "3d"], me=0, history=history,
                              stacks=[2000, 1990, 1980, 0, 2000, 2000, 2000, 2000],
                              bets=[0, 10, 20, 2000, 0, 0, 0, 0])
    action, _ = BOT.act(state, b"")
    check_legal(action, legal)
    assert action.kind == "fold"


def test_flop_decision_is_legal():
    history = BLINDS + [ev("raise", 0, 50), ev("fold", 1), ev("call", 2, 30)] + \
        [ev("fold", i) for i in range(3, 8)] + [ev("board", None, 1), ev("board", None, 2), ev("check", 2)]
    state, legal = make_state(["As", "Ad", "Js"], me=0, history=history, pot=110,
                              stacks=[1950, 1990, 1950, 2000, 2000, 2000, 2000, 2000], bets=[0] * 8,
                              folded=(1, 3, 4, 5, 6, 7), boards=(("Ah", "7d", "2c"), ("Ks", "Qs", "4h")))
    action, _ = BOT.act(state, b"")
    check_legal(action, legal)


def test_discard_returns_one_valid_index():
    state, _ = make_state(["As", "Ad", "Js"], me=0, history=BLINDS, phase="discard", pot=110,
                          stacks=[1950, 1990, 1950, 2000, 2000, 2000, 2000, 2000], bets=[0] * 8,
                          folded=(1, 3, 4, 5, 6, 7), boards=(("Ah", "7d", "2c", "9s"), ("Ks", "Qs", "4h", "2s")))
    action, _ = BOT.act(state, b"")
    assert action.kind == "discard" and len(action.cards) == 1 and action.cards[0] in (0, 1, 2)


@pytest.mark.parametrize("memory", [b"garbage", b"\x00" * 5, b"\xff" * 400])
def test_bad_memory_does_not_crash(memory):
    state, legal = make_state(["7s", "2h", "3d"], me=3, history=BLINDS, **DEEP)
    action, out = BOT.act(state, memory)
    check_legal(action, legal)
    assert isinstance(out, bytes)


def test_memory_round_trip_counts_hands():
    hand = BLINDS + [ev("raise", 3, 60), ev("fold", 4), ev("fold", 5), ev("fold", 6), ev("fold", 7),
                     ev("fold", 0), ev("fold", 1), ev("fold", 2), ev("win", 3, 90)] + \
        [ev("stack", i, 2000) for i in range(8)]
    state, _ = make_state(["7s", "2h", "3d"], me=0, history=BLINDS, events=hand * 3, **DEEP)
    _, memory = BOT.act(state, b"")
    mem = agent.Mem(memory)
    assert mem.hand == 3
    assert mem.s[3][agent.PF] == 3              # seat 3 raised before the flop three times


def test_fallback_when_state_is_broken():
    agent.DEBUG = False
    try:
        broken = NS(phase="betting", can=lambda name: name == "check")
        action, memory = BOT.act(broken, b"abc")
        assert action.kind == "check" and memory == b"abc"
    finally:
        agent.DEBUG = True


def test_average_decision_time_is_under_1ms():
    spots = [make_state(["As", "Ah", "Ks"], me=3, history=BLINDS, **DEEP)[0],
             make_state(["7s", "2h", "3d"], me=3, history=BLINDS, **DEEP)[0]]
    start = time.perf_counter()
    n = 400
    for i in range(n):
        BOT.act(spots[i % 2], b"")
    assert (time.perf_counter() - start) / n < 0.001
