#!/usr/bin/env python3
"""
fetch_market_data.py
Pulls overnight market news, movers, and index data from FMP + X.
Output is injected into Claude Code context to generate a morning script.
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

FMP_KEY = "dENP1cho6YaA38AuKIR36ELzqw8Hjbf4"
FMP_BASE = "https://financialmodelingprep.com/stable"

X_BEARER_RAW = "AAAAAAAAAAAAAAAAAAAAAD9R9AEAAAAAQk%2BQDvI%2BXrTJpZBCAniVaAdTPfE%3DC7nGRdQhloPUhmIES5EfYO1F6Vul9xhbwzrnv4IAWd7N8IlXhK"
X_BEARER = urllib.parse.unquote(X_BEARER_RAW)


def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}


def get_news():
    data = fetch(f"{FMP_BASE}/news/stock?limit=8&apikey={FMP_KEY}")
    if isinstance(data, list) and data:
        return [
            {
                "title": n.get("title", ""),
                "symbol": n.get("symbol", ""),
                "site": n.get("publisher") or n.get("site", ""),
                "text": n.get("text", ""),
            }
            for n in data[:6]
        ]
    return []


def get_gainers_losers():
    gainers = fetch(f"{FMP_BASE}/biggest-gainers?apikey={FMP_KEY}")
    losers = fetch(f"{FMP_BASE}/biggest-losers?apikey={FMP_KEY}")

    def clean(items, n=4):
        if not isinstance(items, list):
            return []
        return [
            {
                "symbol": i.get("symbol"),
                "name": i.get("name", ""),
                "change": round(i.get("changesPercentage", 0), 1),
                "price": i.get("price"),
            }
            for i in items[:n]
        ]

    return clean(gainers), clean(losers)


def get_index(symbol):
    data = fetch(f"{FMP_BASE}/quote?symbol={symbol}&apikey={FMP_KEY}")
    if isinstance(data, list) and data:
        q = data[0]
        return {
            "name": q.get("name", symbol),
            "price": q.get("price"),
            "change_pct": round(q.get("changePercentage", 0), 2),
        }
    return None


def get_x_tweets():
    query = urllib.parse.urlencode({
        "query": "(stock market OR fed OR earnings OR crypto) -is:retweet lang:en",
        "max_results": 10,
        "tweet.fields": "public_metrics",
    })
    url = f"https://api.twitter.com/2/tweets/search/recent?{query}"
    data = fetch(url, headers={"Authorization": f"Bearer {X_BEARER}"})
    tweets = data.get("data", []) if isinstance(data, dict) else []
    return [t.get("text", "")[:200] for t in tweets[:5]] if tweets else []


def fmt_index(idx):
    if not idx:
        return "(unavailable)"
    sign = "+" if idx["change_pct"] >= 0 else ""
    return f"{idx['name']}: {idx['price']:,.2f}  ({sign}{idx['change_pct']}%)"


def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A, %B %d, %Y — %H:%M UTC")

    news = get_news()
    gainers, losers = get_gainers_losers()
    sp500 = get_index("^GSPC")
    nasdaq = get_index("^IXIC")
    dow = get_index("^DJI")
    tweets = get_x_tweets()

    lines = []
    lines.append(f"=== MORNING MARKET DATA — {date_str} ===\n")

    lines.append("--- INDICES ---")
    lines.append(f"  S&P 500:  {fmt_index(sp500)}")
    lines.append(f"  NASDAQ:   {fmt_index(nasdaq)}")
    lines.append(f"  DOW:      {fmt_index(dow)}")

    lines.append("\n--- TOP MARKET NEWS ---")
    if news:
        for i, n in enumerate(news, 1):
            sym = f" [{n['symbol']}]" if n["symbol"] else ""
            blurb = f" — {n['text'][:100]}" if n.get("text") else ""
            lines.append(f"  {i}. {n['title']}{sym} (via {n['site']}){blurb}")
    else:
        lines.append("  (unavailable)")

    lines.append("\n--- TOP GAINERS ---")
    if gainers:
        for g in gainers:
            lines.append(f"  {g['symbol']} ({g['name']}): +{g['change']}%  @ ${g['price']}")
    else:
        lines.append("  (unavailable)")

    lines.append("\n--- TOP LOSERS ---")
    if losers:
        for l in losers:
            lines.append(f"  {l['symbol']} ({l['name']}): {l['change']}%  @ ${l['price']}")
    else:
        lines.append("  (unavailable)")

    if tweets:
        lines.append("\n--- TRENDING ON X (FINANCE) ---")
        for t in tweets:
            lines.append(f"  • {t}")

    lines.append("""
=== YOUR JOB, CLAUDE ===
Using the data above, write a punchy morning finance video script.

Rules:
- 80-120 words (reads in 30-45 seconds at a natural, conversational pace)
- Start with "Morning, [day] [month] [date]." — e.g. "Morning, Tuesday June 2nd." Use the date from the market data header above.
- Sound like a charismatic human host — warm, sharp, NOT robotic
- Humor should be dry, deadpan, or sardonic — the kind of thing that makes someone smirk, not groan. No puns, no similes, no corny comparisons. Just sharp observations delivered straight.
- Hit the biggest index moves, 1-2 news stories, and the wildest gainer or loser
- Short punchy sentences. Flowing speech — no bullet points, no headers
- End with a memorable zinger, challenge, or teaser
- Output ONLY the final script — no labels, no preamble, no meta-commentary
""")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
