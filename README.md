# no-limit-poker-bot

Team **leMinecraft**'s bot for the No Limit 2026 poker bot competition (Pittsburgh regional).

The game is "Pittsburgh": no-limit hold'em with three hole cards, two boards, and one
discard after the turn. Each pot is split in half, one half per board. Tables are
8-player sit-and-gos that pay 50 / 30 / 20 points to the top three, so survival matters
more than chips.

This repo holds **bot9**, the version described below.

## Layout

```
submission/agent.py     the bot (single file, upload this)
tests/test_agent.py     tests that run without the competition SDK
benchmarks/results.md   real round scores for each version
```

## How the bot works

Every decision must return within 1 ms, so the bot only does table lookups and a few
hand evaluations.

- **Hand strength table.** Every 3-card starting hand has a rank and its all-in equity
  against six opponent ranges. The table is packed inside `agent.py`.
- **Bubble factor.** A lookup table of ICM place probabilities turns pot odds into the
  equity needed to risk chips: `need = BF * call / (pot + BF * call)`. It uses each
  table's own payouts.
- **Before the flop.** Push or fold at 12 big blinds or less. Above that it opens by
  position, re-shoves over raises at 25 big blinds or less, and re-raises small when
  deeper. Ranges were set from our own results in earlier rounds.
- **After the flop.** It samples opponent hands and counts how many it beats on each
  board, then bets, calls or folds on the average of the two boards.
- **Discard.** It keeps the two cards that win most often over sampled river cards.
- **Opponent memory.** 266 bytes per table: 14 counters per seat (how often they raise,
  shove, call shoves, fold to bets, re-raise) plus stack sizes.

If anything goes wrong inside a decision, the bot checks or folds instead of crashing.

## Running the tests

```sh
pip install -r requirements.txt pytest
pytest tests
```

The competition SDK is not on the public package index. The tests install a small
stand-in for it, so they run anywhere. They check that the bot returns legal actions,
survives bad memory, and averages under 1 ms per decision.

## Submitting

Upload `submission/agent.py` on the team page. Before uploading a changed file, run the
official `poker-agent check` and `poker-agent play` from the starter kit.

## Limits

- The hand-strength and bubble-factor tables were generated offline by simulation. The
  script that built them is not in this repo, so the tables cannot be rebuilt from here.
- The ranges are tuned to the field we met in this event. They are not a general
  solution to the game.
- Hand histories and the starter kit are not included.

## License

MIT. See `LICENSE`.
