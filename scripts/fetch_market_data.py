#!/usr/bin/env python3
"""
fetch_market_data.py
Pulls top headline news (RSS) + market context (FMP).
Output is injected into Claude Code context to generate a TikTok morning news script.
"""

import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FMP_KEY = "dENP1cho6YaA38AuKIR36ELzqw8Hjbf4"
FMP_BASE = "https://financialmodelingprep.com/stable"

X_BEARER_RAW = "AAAAAAAAAAAAAAAAAAAAAD9R9AEAAAAAQk%2BQDvI%2BXrTJpZBCAniVaAdTPfE%3DC7nGRdQhloPUhmIES5EfYO1F6Vul9xhbwzrnv4IAWd7N8IlXhK"
X_BEARER = urllib.parse.unquote(X_BEARER_RAW)

RSS_FEEDS = [
    ("AP News",      "https://feeds.apnews.com/rss/apf-topnews"),
    ("Reuters",      "https://feeds.reuters.com/reuters/topNews"),
    ("BBC",          "http://feeds.bbci.co.uk/news/rss.xml"),
    ("NPR",          "https://feeds.npr.org/1001/rss.xml"),
]


def fetch_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}


def fetch_rss(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            root = ET.fromstring(r.read())
    except Exception:
        return []

    items = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for item in root.iter("item"):
        title = item.findtext("title", "").strip()
        desc  = item.findtext("description", "").strip()
        if title:
            items.append({"title": title, "desc": desc[:120] if desc else ""})
        if len(items) >= 4:
            break
    return items


def get_headlines():
    seen, results = set(), []
    for source, url in RSS_FEEDS:
        for item in fetch_rss(url):
            t = item["title"]
            if t not in seen:
                seen.add(t)
                results.append({"source": source, "title": t, "desc": item["desc"]})
        if len(results) >= 10:
            break
    return results[:8]


def get_fmp_news():
    data = fetch_json(f"{FMP_BASE}/news/stock?limit=6&apikey={FMP_KEY}")
    if isinstance(data, list) and data:
        return [
            {"title": n.get("title", ""), "symbol": n.get("symbol", ""), "text": n.get("text", "")[:100]}
            for n in data[:4]
        ]
    return []


def get_index(symbol):
    data = fetch_json(f"{FMP_BASE}/quote?symbol={symbol}&apikey={FMP_KEY}")
    if isinstance(data, list) and data:
        q = data[0]
        return {"name": q.get("name", symbol), "price": q.get("price"), "change_pct": round(q.get("changePercentage", 0), 2)}
    return None


def fmt_index(idx):
    if not idx:
        return "(unavailable)"
    sign = "+" if idx["change_pct"] >= 0 else ""
    return f"{idx['name']}: {idx['price']:,.2f} ({sign}{idx['change_pct']}%)"


def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A, %B %d, %Y — %H:%M UTC")

    headlines = get_headlines()
    fmp_news  = get_fmp_news()
    sp500     = get_index("^GSPC")
    nasdaq    = get_index("^IXIC")
    dow       = get_index("^DJI")

    lines = []
    lines.append(f"=== MORNING NEWS DATA — {date_str} ===\n")

    lines.append("--- TOP HEADLINES (RSS) ---")
    if headlines:
        for i, h in enumerate(headlines, 1):
            lines.append(f"  {i}. [{h['source']}] {h['title']}")
            if h["desc"]:
                lines.append(f"     {h['desc']}")
    else:
        lines.append("  (unavailable)")

    lines.append("\n--- MARKET CONTEXT ---")
    lines.append(f"  {fmt_index(sp500)}")
    lines.append(f"  {fmt_index(nasdaq)}")
    lines.append(f"  {fmt_index(dow)}")

    if fmp_news:
        lines.append("\n--- FINANCE HEADLINES ---")
        for n in fmp_news:
            sym = f" [{n['symbol']}]" if n["symbol"] else ""
            lines.append(f"  • {n['title']}{sym}")
            if n["text"]:
                lines.append(f"    {n['text']}")

    lines.append("""
=== YOUR JOB, CLAUDE ===
Write a TikTok morning news script using the headlines above.

Format:
1. HOOK — One punchy sentence that makes someone stop scrolling. Pull it from the biggest or most surprising headline. No question hooks. State something that demands attention.
2. NEWS — Cover the 3-4 biggest stories in rapid-fire order. One to two sentences each. Facts first, then a brief dry observation if it earns one.
3. CLOSER — One sharp line that wraps it up or teases what to watch next.

Rules:
- 80-120 words total (30-45 seconds at talking pace)
- Start with "Morning, [Day] [Month] [date]." then immediately the hook on the next beat
- Tone: direct, fast, confident — like a news anchor who also has a personality
- Humor: dry and sardonic only. No puns, no forced comparisons, no corny jokes.
- No bullet points — flowing speech throughout
- Output ONLY the final script, nothing else
""")

    sys.stdout.buffer.write("\n".join(lines).encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
