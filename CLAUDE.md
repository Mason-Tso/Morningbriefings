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
| RSS — General (AP, Reuters, BBC, NPR) | Top general headlines of the morning |
| RSS — Politics (NPR Politics, The Hill, BBC Politics) | Legislation, federal spending, policy moves |
| RSS — Science (NPR Science, STAT News, ScienceDaily) | Biotech/science breakthroughs and catalysts |
| Financial Modeling Prep (FMP) | S&P 500, NASDAQ, DOW quotes; finance headlines |

Headlines are grouped into **General / Politics / Science** sections in the output so policy and biotech catalysts surface alongside general news.

## Script format (strictly enforced)

- **60-75 words** (under 30 seconds — shorter = more watch-through)
- **TikTok format: Hook → 2-3 rapid-fire stories → specific call to action**
- Starts directly with the hook — no date, no "Morning", no intro. First word = first punch.
- Hook is a single declarative statement pulled from the biggest headline. No questions.
- Prioritise news that moves markets — jobs data, Fed signals, major legislation, geopolitical events with economic impact
- After the biggest story, one sentence on what it means for markets or the economy
- Tone: professional and confident — complete sentences, like a polished news anchor
- Humor: dry and sardonic only if it earns it. No puns, no forced comparisons, no corny jokes.
- Closes with a specific, direct call to action. Market is already open — frame it accordingly. Never say "stay informed."
- No bullet points — flowing speech throughout
- **Tie every story to a tradable sector** — after each story, name the sector(s) it moves (e.g. "that kind of federal spending commitment moves defense and corrections sectors"). The CTA names the specific sectors "in play right now." See the EXEMPLAR block in `fetch_market_data.py` for the target style.

## API keys

Stored directly in `scripts/fetch_market_data.py`. Rotate via FMP dashboard if they expire.

- **FMP**: Financial Modeling Prep — `stable/` API endpoints
- **RSS feeds**: No key required (AP, Reuters, BBC, NPR)

## Hook behavior

When you type `go`, `.claude/settings.json` matches the message via `(?i)^go$` and runs `scripts/fetch_market_data.py`. The script's stdout is injected into Claude's context as a system message, then Claude writes the script.

## Adding features

- **More RSS sources**: Add entries to the `RSS_FEEDS` list in `fetch_market_data.py`
- **Crypto prices**: FMP `stable/quote?symbol=BTC-USD` returns empty — use a dedicated crypto API
- **Save scripts**: Add `--save` flag to `fetch_market_data.py` to write output to `scripts/output/`
