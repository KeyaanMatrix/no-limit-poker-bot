# Results

Real scores from competition rounds, computed from our own hand-history downloads.
An even share is 12.5 points per table (100 points split among 8 players).

| Version | Tables | Points per table | 1st | 2nd | 3rd |
|---|---|---|---|---|---|
| First bot (hand-written rules) | 5,190 | 5.63 | 6.4% | 5.1% | 4.6% |
| Table-driven rewrite | 5,147 | 13.38 | 10.6% | 15.2% | 17.6% |
| + ranges set from results, re-shoves | 5,050 | 16.11 | 15.9% | 16.3% | 16.4% |
| bot7: + wider shove calls | 10,003 | 16.95 | 21.7% | 12.5% | 11.7% |
| bot7, second round | 5,005 | 16.40 | 20.5% | 12.2% | 12.4% |
| bot8: + small re-raises when deep | 5,000 | 16.64 | 21.6% | 12.0% | 11.1% |
| bot8, second file | 5,005 | 16.01 | 20.2% | 13.0% | 10.1% |
| **bot9** (this repo) | - | not measured | - | - | - |

## Notes

- bot9 tightened the opening ranges and widened the big blind re-raise after bot8's
  rounds. We have not analysed a hand history from bot9, so it has no score here.
- No version had a failed decision (timeout, error or illegal action) in these rounds.
- In the rounds above, the best team we met scored between about 18 and 21 points per
  table. bot7 and bot8 placed between about 5th and 13th of roughly 110 teams. Those
  ranks count only teams we met often enough to rank, on the tables we played, so they
  are not the official standings.
- Scores move by a few tenths of a point between rounds from luck alone, and the field
  changed between rounds as teams updated their bots.
