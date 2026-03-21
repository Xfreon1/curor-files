# WTF Dashboard — Setup Guide

## Requirements
- Python 3.9+ (for `zoneinfo` stdlib)
- Windows (for Now Playing / SMTC widget)

## Install

```
cd F:\wtf-dashboard
pip install -r requirements.txt
```

## Configure

Edit `config.py`:

1. **Weather** — Get a free API key at https://openweathermap.org/api
   Set `WEATHER_API_KEY = "your_key_here"`

2. **Cities** — `WEATHER_CITIES = ["Talsi,LV", "Riga,LV"]` (OpenWeatherMap city format)

3. **Countdown** — Set `COUNTDOWN_DATE = "2026-12-31"` (YYYY-MM-DD)

4. **RSS** — Set `RSS_URL` to any RSS feed URL

5. **Reddit** — Set `REDDIT_SUBS` to a list of subreddit names (no r/ prefix)

6. **Custom command** — Set `CUSTOM_COMMAND` to any shell command to run in Screen 3

## Run

```
python dashboard.py
```
or double-click `run.bat`

## Controls

| Key | Action |
|-----|--------|
| `1` | Screen 1 — Main |
| `2` | Screen 2 — Markets |
| `3` | Screen 3 — News |
| `Tab` | Next panel |
| `Shift+Tab` | Previous panel |
| `q` | Quit |

### Todo List (Screen 1)
Focus the Todo panel, then:
| Key | Action |
|-----|--------|
| `a` | Add item |
| `d` | Delete selected item |
| `Space` | Toggle done/undone |

## API Keys Required
- **OpenWeatherMap** — free tier, 60 calls/min, get at openweathermap.org

## No Key Required
- CoinGecko (crypto prices)
- Yahoo Finance via yfinance (stocks)
- Hacker News Firebase API
- Reddit public .json endpoint
- RSS feeds
- Windows SMTC (Now Playing)

## Troubleshooting

**Now Playing shows nothing** — Make sure something is playing in YouTube Music, Spotify, etc. The widget uses Windows SMTC (System Media Transport Controls).

**Weather shows placeholder** — Set your API key in config.py.

**Stocks/Crypto show errors** — Check your internet connection. yfinance and CoinGecko are free but rate-limited.

**winmedia-controller won't install** — This is Windows-only. If on another OS, the Now Playing widget will show a fallback message.
