# MorningVids — Claude Code Context

## What this project does

Automated morning finance video script generator. Type **"go"** in Claude Code and a live market data fetch runs automatically, injecting real data into context. Claude then writes a 30-45 second human-sounding script with jokes and market highlights.

## How to use

1. Open this project in Claude Code
2. Type `go` and hit Enter
3. Claude fetches live data and writes your morning script

## Project structure

```
scripts/
  fetch_market_data.py   # Fetches FMP + X data, outputs context for Claude
.claude/
  settings.json          # UserPromptSubmit hook — triggers on "go"
CLAUDE.md                # This file
```

## Data sources

| Source | What it pulls |
|--------|--------------|
| Financial Modeling Prep (FMP) | S&P 500, NASDAQ, DOW quotes; top news; biggest gainers & losers |
| X (Twitter) API | Trending finance tweets (if available on current tier) |

## Script rules (enforced via hook output)

- 80-120 words (30-45 seconds at natural speaking pace)
- Charismatic human host tone — no robotic language
- 1-2 genuine jokes tied to actual data points
- Covers index moves, 1-2 news stories, wildest gainer or loser
- Punchy flowing speech — no bullet points
- Memorable closer every time

## API keys

Stored directly in `scripts/fetch_market_data.py`. Rotate via FMP dashboard and X developer portal if they expire.

- **FMP**: Financial Modeling Prep — `stable/` API endpoints (not v3)
- **X Bearer**: URL-decoded in script at runtime

## Hook behavior

When you type `go`, `.claude/settings.json` matches the message via `(?i)^go$` and runs `scripts/fetch_market_data.py`. The script's stdout is injected into Claude's context as a system message, then Claude writes the script.

## Adding features

- **Crypto prices**: FMP `stable/quote?symbol=BTC-USD` returns empty — use a dedicated crypto API
- **More X data**: Upgrade X API tier for broader search access
- **Save scripts**: Add `--save` flag to `fetch_market_data.py` to write output to `scripts/output/`
