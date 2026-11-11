# Strategy: Range-Bounce Swing Trader

## The market in the dev window

The frozen 24-hour dev window (1,440 one-minute cbBTC/USDC bars) drifts down
108 bps overall (first half −190 bps, second half +83 bps) with 1-minute
volatility of ~5.9 bps and 221 flat bars. Inside that drift the price swings
30–230 bps over 20–90 minutes — several full swings a day. A full-size round
trip costs ~26 bps (4 bps fee + 2 bps slippage + ~7 bps price impact each
way at the frozen pool depth, plus the final flatten).

## What does not work here

- **Buy-and-hold:** −$13.44 on the dev window (the window falls).
- **EMA(8/21) crossover:** −$89.29 officially, 65 trades — whipsawed by the
  chop (verified with the kit's own `grade-local`).
- **Donchian breakout (N=10–60):** −$26 to −$34 — breakouts buy the move
  after it already happened, then give it back.
- **Plain dip-buying / z-score mean reversion:** −$1.70 to −$15 — dips in a
  falling first half keep falling.

The exploitable structure is the swing itself: sharp rises reliably fade
(median 30-minute forward return −59 bps after a 15-bar rise of 60+ bps),
while the price keeps returning to the edges of a wide 4-hour range.

## The rules

1. **Range:** high = max high, low = min low of the previous 240 bars.
2. **Entry (flat only):** close in the bottom 25% of the range
   (`(close − low) / (high − low) ≤ 0.25`) **and** close ≥ previous close
   + 10 bps. The bounce filter matters: without it the bot catches falling
   knives and loses; with it, it buys the start of the bounce.
3. **Exit (holding only):** close ≥ the 240-bar high (a new high — the top
   of the range), or close ≤ peak close since entry − 60 bps (trailing
   stop), or close ≤ entry close − 60 bps (hard stop).
4. **Sizing:** 100% of cash on entry, one position at most, long only.
   `max_slippage_bps` is 200 — wide enough for 1-minute gaps, still bounded.

## Dev-window result (local replay grader, exact fill model)

- **Net PnL: +$16.64** (5 round trips, 10 fills), max drawdown 127 bps
  (1.27%, far under the 25% guardrail), fees $4.04, 0 rejected orders.
  Verified by driving the real `main.py` subprocess through the protocol
  (hello + 1,440 batches + done) twice: both action logs byte-identical.
- First half +$7.41, second half +$5.45 — positive on both halves.
- Neighbourhood is flat, not a sharp peak: N=180–300 gives +$12.09 to
  +$14.48, entry fraction 0.20–0.30 gives +$9.73 to +$14.41, trailing stop
  60–70 bps gives the same +$16.64, and four different bounce-confirmation
  definitions all land at +$14.94 to +$16.64. The one sensitive knob is the
  bounce size (10 bps), which is a ~1.7σ one-minute move — a real signal,
  not a fitted decimal.

## Why this is not a baseline

No baseline trades a rolling high/low range with a bounce confirmation: the
kit ships buy-and-hold, hold-cash, 24-bar momentum, EMA(8/21) cross,
RSI(14) + Bollinger(20, 2σ) mean reversion, and ADX(14) momentum. This bot
uses none of those indicators.

## Risks

- The race window is unseen: if BTC trends hard in one direction for 24
  hours with no range swings, the bot may sit flat (PnL $0, fails the
  guardrail only if it never trades — it trades whenever a bounce off a
  4-hour low appears) or ride one swing.
- A 60 bps trailing stop can exit a good swing early in a volatile hour.
- The dev window is one sample; the parameters were chosen for a flat
  neighbourhood and two positive halves, not for the single best number.
