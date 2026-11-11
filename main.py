"""Range-bounce swing trader for cbBTC/USDC, agent-fun/bars-replay/v1.

Idea: on 1-minute bars the price spends most of a 24h window swinging inside a
wide range (the dev window's swings run 30-230 bps over 20-90 minutes) while
paying ~26 bps per full-size round trip. Trend breakouts buy the move after it
already happened; instead this bot buys the low of the range and sells the high:

- Range: the highest high and lowest low of the previous 240 bars (4 hours).
- Entry (flat only): the latest close sits in the bottom quarter of that range
  AND the close just bounced at least 10 bps off the previous close, so the
  bot buys the start of the bounce, not a still-falling knife.
- Exit (holding only): the close reaches a new 240-bar high (the top of the
  range), or a 60 bps trailing stop below the highest close since entry, or a
  60 bps hard stop below the entry close.

One position at most, full cash on entry, long only. All decisions are integer
math on the bars themselves: no clock, no network, no files, no randomness,
so two runs on the same data produce the same orders byte for byte.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
RANGE_BARS = 240          # 4 hours of 1-minute bars
ENTRY_FRACTION_BPS = 2500  # enter only in the bottom quarter of the range
BOUNCE_BPS = 10           # entry needs a bounce of at least this vs prev close
TRAIL_BPS = 60            # trailing stop below the peak close since entry
STOP_BPS = 60             # hard stop below the entry close
MAX_SLIPPAGE_BPS = 200    # wide enough for 1-minute gaps, still bounded


class SwingBot:
    def __init__(self):
        self.closes = []
        self.highs = []
        self.lows = []
        self.entry_close = None
        self.peak_close = None

    def on_batch(self, state, batch):
        bar = None
        for b in batch["bars"]:
            if b["symbol"] == SYMBOL:
                bar = b
                break
        if bar is None:
            return []
        close = int(bar["c"])
        self.closes.append(close)
        self.highs.append(int(bar["h"]))
        self.lows.append(int(bar["l"]))

        holding = state.positions.get(SYMBOL)
        if holding is None:
            self.entry_close = None
            self.peak_close = None
            if len(self.closes) < RANGE_BARS + 1:
                return []
            lows = self.lows[-RANGE_BARS - 1:-1]
            highs = self.highs[-RANGE_BARS - 1:-1]
            low = min(lows)
            high = max(highs)
            if high <= low:
                return []
            # Position of the close inside the range, in bps from the low.
            fraction = (close - low) * 10000 // (high - low)
            if fraction > ENTRY_FRACTION_BPS:
                return []
            prev_close = self.closes[-2]
            if close * 10000 < prev_close * (10000 + BOUNCE_BPS):
                return []
            # The harness rejects a buy under 1 USDC; with full-cash sizing this
            # only matters if a previous fill left dust, but never send it.
            if state.cash < 1000000:
                return []
            self.entry_close = close
            self.peak_close = close
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": state.cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]

        if self.entry_close is None:
            self.entry_close = close
            self.peak_close = close
        if close > self.peak_close:
            self.peak_close = close
        lows = self.lows[-RANGE_BARS - 1:-1]
        highs = self.highs[-RANGE_BARS - 1:-1]
        low = min(lows)
        high = max(highs)
        at_new_high = close >= high
        trail_hit = close * 10000 <= self.peak_close * (10000 - TRAIL_BPS)
        stop_hit = close * 10000 <= self.entry_close * (10000 - STOP_BPS)
        if at_new_high or trail_hit or stop_hit:
            self.entry_close = None
            self.peak_close = None
            return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []


makefun_bars.run(SwingBot().on_batch)
