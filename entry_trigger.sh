#!/usr/bin/env bash
# Entry trigger: fires ONE market order when price crosses ENTRY_ABOVE (self-disables via flag).
# Idempotent: the flag file prevents double entries across cron runs.
set -u
SYMBOL=${SYMBOL:-BTCUSDT}; ENTRY_ABOVE=${ENTRY_ABOVE:-87000}
QTY_USD=${QTY_USD:-600}; LEV=${LEV:-40}
FLAG=${FLAG:-$HOME/.crypto-ops/.entry-done}; CLIENT=${CLIENT:-$HOME/crypto-ops/bitunix_client.py}
PY=${PY:-python3}
mkdir -p "$(dirname "$FLAG")"
[ -f "$FLAG" ] && exit 0
price=$(curl -s -m 10 "https://fapi.bitunix.com/api/v1/futures/market/tickers?symbols=$SYMBOL" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['data'][0]['lastPrice'])" 2>/dev/null)
[ -z "$price" ] && exit 0
hit=$("$PY" -c "print(1 if float('$price') >= float('$ENTRY_ABOVE') else 0)")
[ "$hit" = "1" ] || exit 0
touch "$FLAG"
qty=$("$PY" -c "print(round(float('$QTY_USD') / float('$price'), 4))")
"$PY" "$CLIENT" open "$SYMBOL" SELL OPEN "$qty" "$LEV"
exit 0
