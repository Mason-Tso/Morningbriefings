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

# (category, source, url) — categories group the output so policy + science
# catalysts surface alongside general news for the script.
RSS_FEEDS = [
    ("General",  "AP News",       "https://feeds.apnews.com/rss/apf-topnews"),
    ("General",  "Reuters",       "https://feeds.reuters.com/reuters/topNews"),
    ("General",  "BBC",           "http://feeds.bbci.co.uk/news/rss.xml"),
    ("General",  "NPR",           "https://feeds.npr.org/1001/rss.xml"),
    ("Politics", "NPR Politics",  "https://feeds.npr.org/1014/rss.xml"),
    ("Politics", "The Hill",      "https://thehill.com/rss/syndicator/19110"),
    ("Politics", "BBC Politics",  "http://feeds.bbci.co.uk/news/politics/rss.xml"),
    ("Science",  "NPR Science",   "https://feeds.npr.org/1007/rss.xml"),
    ("Science",  "STAT News",     "https://www.statnews.com/feed/"),
    ("Science",  "ScienceDaily",  "https://www.sciencedaily.com/rss/top/science.xml"),
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
    """Return {category: [headlines]} with per-category caps, deduped globally."""
    seen = set()
    grouped = {"General": [], "Politics": [], "Science": []}
    caps = {"General": 6, "Politics": 4, "Science": 4}
    for category, source, url in RSS_FEEDS:
        if len(grouped[category]) >= caps[category]:
            continue
        for item in fetch_rss(url):
            t = item["title"]
            if t not in seen:
                seen.add(t)
                grouped[category].append({"source": source, "title": t, "desc": item["desc"]})
            if len(grouped[category]) >= caps[category]:
                break
    return grouped


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

    section_titles = {
        "General":  "--- TOP HEADLINES (RSS) ---",
        "Politics": "--- POLITICS & LEGISLATION ---",
        "Science":  "--- SCIENCE & BIOTECH ---",
    }
    any_headlines = any(headlines.get(c) for c in section_titles)
    if any_headlines:
        for cat, title in section_titles.items():
            items = headlines.get(cat) or []
            if not items:
                continue
            lines.append(title)
            for i, h in enumerate(items, 1):
                lines.append(f"  {i}. [{h['source']}] {h['title']}")
                if h["desc"]:
                    lines.append(f"     {h['desc']}")
            lines.append("")
    else:
        lines.append("--- TOP HEADLINES (RSS) ---")
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

Pick the BIGGEST, most genuinely newsworthy headlines of the morning — judge
by actual significance, drawing from ALL sections (general, politics, science,
finance) however the day falls. Do NOT force politics or any single category;
some mornings the top stories are markets, some are policy, some are a major
company or world event. Once you've picked the biggest stories, connect each to
a tradable sector or asset where there's a real link (don't force a stretch).

Format:
1. HOOK — One punchy sentence pulled from the single biggest story of the morning. Lead with the NARRATIVE — a company, analyst, or policy angle (e.g. "Wall Street is piling into Apple ahead of Monday's WWDC..."). No question hooks.
2. NEWS — Cover ~2 stories, chosen purely by how big they are. After each, name the specific sector(s) or asset it moves when there's a genuine market link (e.g. "that kind of federal spending commitment moves defense and corrections sectors", "that's a major catalyst for biotech").
3. CLOSER — A direct call to action naming the specific sectors/assets to watch TODAY, framed as "in play right now."

Rules:
- 60-75 words total (under 30 seconds at talking pace — shorter = more watch-through)
- Start directly with the hook — no date, no "Morning", no intro. First word = first punch.
- Do NOT mention index moves (no "NASDAQ down 3%", "S&P up", "Dow off a percent", etc.). The index numbers are context for YOU only — keep the script to company, policy, sector, and analyst narratives.
- Every story must connect to a tradable sector or asset.
- Tone: professional and confident — complete sentences throughout, like a polished news anchor.
- End with a specific CTA naming sectors in play right now. Never say "stay informed" or anything vague.
- Humor: dry and sardonic only if it earns it. No puns, no forced comparisons, no corny jokes.
- No bullet points — flowing speech throughout.
- Output ONLY the final script, nothing else.

EXEMPLARS (match this style — either shape is valid depending on the day's news):

A) Policy / sector-driven morning:
The Senate passed a $70 billion immigration enforcement bill overnight after an 18-hour vote, funding ICE and Border Patrol through the end of Trump's term. That kind of federal spending commitment moves defense and corrections sectors. Cambridge scientists also announced the world's first AI-designed vaccine, successfully tested and potentially effective against entire families of viruses — that's a major catalyst for biotech. Watch healthcare and biotech stocks today, both stories are in play right now.

B) Stock / market-action morning (name specific tickers, cite analyst calls, read sentiment, end with a dated CTA — but NO index numbers):
Morgan Stanley is calling Apple a major AI breakout candidate heading into WWDC next week, with Siri 2.0 potentially driving the next leg up. Tech investors are leaning in, betting the keynote finally proves Apple can compete in AI. Intel, meanwhile, announced an AI partnership with Foxconn and its stock is still falling — which tells you how the market feels about Intel's execution right now. Watch Apple into WWDC on June 8th — that's the trade of next week.

C) Catalyst-driven morning — hook leads with the NARRATIVE, tension comes from the stakes, not the tape:
Wall Street is piling into Apple ahead of Monday's WWDC, betting an AI-powered Siri 2.0 becomes Tim Cook's legacy and the next leg up for the stock. This is Cook's final keynote as CEO, and tech investors are nervous — if Siri underwhelms, the whole sector's rebound stalls. Watch Apple into WWDC on June 8th; that's the trade of the week.
""")

    sys.stdout.buffer.write("\n".join(lines).encode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()
