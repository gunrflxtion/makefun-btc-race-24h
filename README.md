# Range-Bounce Swing Trader — cbBTC/USDC

A bot for the make.fun competition "Race a BTC trading bot live for 24 hours"
(`btc-race-24h-20261111-0801`). It trades Coinbase Wrapped BTC against USDC on
1-minute bars, long only, starting from $1,000 of paper money.

## How it works

On 1-minute bars the price spends most of a 24-hour window swinging inside a
wide range while a full-size round trip costs about 26 bps in fees, slippage
and price impact. This bot buys the low of the range and sells the high:

- **Range:** highest high and lowest low of the previous 240 bars (4 hours).
- **Entry:** the latest close is in the bottom quarter of that range **and**
  the close just bounced at least 10 bps off the previous close.
- **Exit:** the close reaches a new 240-bar high, or a 60 bps trailing stop
  below the highest close since entry, or a 60 bps hard stop below entry.

One position at most, full cash on entry. See `STRATEGY.md` for the full
reasoning, the dev-window result and the robustness checks.

## Run it

Python 3.13, standard library only. The bot speaks `agent-fun/bars-replay/v1`
(newline-delimited JSON on stdin/stdout) through the vendored kit shim in
`vendor/makefun_bars.py`, a byte-identical copy of the kit's
`sdk/makefun_bars.py`.

## License

MIT — see `LICENSE`.
