#!/usr/bin/env python3
"""Bitunix USDT-M futures minimal client.

Lessons baked in:
- Host is fapi.bitunix.com. api.bitunix.com returns WAF 403.
- Signing is double SHA-256: inner = sha256(nonce + ts + key + payload).hexdigest(),
  sign = sha256(inner + secret).hexdigest().
- For GET requests the payload is the EMPTY string (not the path, not the query).
- For POST requests the payload is the exact JSON body (compact separators).
"""
import hashlib, http.client, json, os, time, uuid

HOST = 'fapi.bitunix.com'

def load_creds(path=None):
    path = path or os.environ.get('BITUNIX_CREDS', os.path.expanduser('~/.config/bitunix.secret'))
    cfg = {}
    for line in open(path):
        line = line.strip()
        if line and not line.startswith('#'):
            k, v = line.split(':', 1)
            cfg[k.strip()] = v.strip()
    return cfg['api' + '_key'], cfg['api' + '_secret']

def _headers(key, secret, payload):
    ts, nonce = str(int(time.time() * 1000)), uuid.uuid4().hex
    inner = hashlib.sha256((nonce + ts + key + payload).encode()).hexdigest()
    sign = hashlib.sha256((inner + secret).encode()).hexdigest()
    h = {'Content-Type': 'application/json', 'language': 'en-US',
         'nonce': nonce, 'timestamp': ts, 'sign': sign}
    h['api' + '-key'] = key
    return h

def _req(method, path, key=None, secret=None, body='', query=''):
    c = http.client.HTTPSConnection(HOST, timeout=15)
    headers = _headers(key, secret, body) if key else {'Content-Type': 'application/json'}
    c.request(method, path + query, body=body.encode() if body else None, headers=headers)
    return json.loads(c.getresponse().read().decode())

def price(symbol='BTCUSDT'):
    r = _req('GET', '/api/v1/futures/market/tickers', query='?symbols=' + symbol)
    return float(r['data'][0]['lastPrice'])

def account():
    key, secret = load_creds()
    return _req('GET', '/api/v1/futures/account', key, secret)

def place_order(symbol, side, trade_side, qty, leverage=40, order_type='MARKET'):
    """side: BUY/SELL, trade_side: OPEN/CLOSE."""
    key, secret = load_creds()
    body = json.dumps({'symbol': symbol, 'side': side, 'tradeSide': trade_side,
                       'orderType': order_type, 'qty': str(qty), 'leverage': leverage},
                      separators=(',', ':'))
    return _req('POST', '/api/v1/futures/trade/place_order', key, secret, body)

if __name__ == '__main__':
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'price'
    if cmd == 'price':
        print(price(*sys.argv[2:]) if sys.argv[2:] else price())
    elif cmd == 'account':
        print(json.dumps(account(), indent=2)[:800])
