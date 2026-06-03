# MorningVids — Claude Code Context

## What this project does

Automated morning TikTok news script generator. Type **"go"** in Claude Code and a live data fetch runs automatically, pulling top headline news and market context. Claude then writes a 30-45 second TikTok-style script with a hook-first format.

## How to use

1. Open this project in Claude Code
2. Type `go` and hit Enter
3. Claude fetches live data and writes your morning script

## Project structure

```
scripts/
  fetch_market_data.py   # Fetches RSS headlines + FMP market data, outputs context for Claude
.claude/
  settings.json          # UserPromptSubmit hook — triggers on "go"
CLAUDE.md                # This file
```

## Data sources

| Source | What it pulls |
|--------|--------------|
| RSS (AP, Reuters, BBC, NPR) | Top general headlines of the morning |
| Financial Modeling Prep (FMP) | S&P 500, NASDAQ, DOW quotes; finance headlines |
| X (Twitter) API | Trending finance tweets (if available on current tier) |

## Script rules (enforced via hook output)

- Opens with "Morning, [Day] [Month] [Date]." — e.g. "Morning, Tuesday June 2nd."
- 80-120 words (30-45 seconds at natural speaking pace)
- TikTok format: Hook → 3-4 rapid-fire stories → sharp closer
- Hook is a single statement pulled from the biggest headline — no questions
- Tone: direct, fast, confident — like a news anchor with a personality
- Humor is dry and sardonic — sharp observations delivered straight. No puns, no corny comparisons.
- No bullet points — flowing speech throughout

## API keys

Stored directly in `scripts/fetch_market_data.py`. Rotate via FMP dashboard and X developer portal if they expire.

- **FMP**: Financial Modeling Prep — `stable/` API endpoints
- **X Bearer**: URL-decoded in script at runtime
- **RSS feeds**: No key required (AP, Reuters, BBC, NPR)

## Hook behavior

When you type `go`, `.claude/settings.json` matches the message via `(?i)^go$` and runs `scripts/fetch_market_data.py`. The script's stdout is injected into Claude's context as a system message, then Claude writes the script.

## Adding features

- **More RSS sources**: Add entries to the `RSS_FEEDS` list in `fetch_market_data.py`
- **Crypto prices**: FMP `stable/quote?symbol=BTC-USD` returns empty — use a dedicated crypto API
- **Save scripts**: Add `--save` flag to `fetch_market_data.py` to write output to `scripts/output/`
