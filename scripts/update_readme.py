import json, datetime, os, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def fmt_num(n):
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M'
    if n >= 1_000:     return f'{n/1_000:.1f}k'
    return str(n)

def delta_badge(d):
    if d > 500:   return f'🔥 +{fmt_num(d)}'
    if d > 0:     return f'↑ +{fmt_num(d)}'
    if d < 0:     return f'↓ {fmt_num(d)}'
    return '—'

def main():
    try:
        latest_file = Path('data/latest.json')
        if not latest_file.exists():
            print("data/latest.json not found. Run fetch.py first.")
            return
            
        data = json.loads(latest_file.read_text(encoding='utf-8'))
        date = data.get('date', datetime.date.today().isoformat())
        repos = data.get('repos', [])
        hf    = data.get('hf_trending', [])
        pypi  = data.get('pypi', [])
        arena = data.get('lmsys_arena', [])
        
        # Cache-busting timestamp
        ts = int(time.time())
        
        # ─── GitHub velocity table ───────────────────────────────────
        repo_rows = []
        for r in repos[:10]:
            safe = r['repo'].replace('/', '_')
            # Add cache-busting query param
            spark = f'![spark](charts/{safe}_spark.png?v={ts})'
            repo_rows.append(
                f"| [{r['repo']}](https://github.com/{r['repo']}) | ⭐ {fmt_num(r['stars'])} | {delta_badge(r['delta_24h'])} | {spark} |"
            )
            
        repo_table = '\n'.join([
            '| Repository | Stars | 24h Change | Trend |',
            '|---|---|---|---|',
        ] + repo_rows)
        
        # ─── LMSYS Arena table ───────────────────────────────────────
        arena_rows = [f'| {a["rank"]} | {a["model"]} | {a["elo"]} |'
                      for a in arena[:8]]
        arena_table = '\n'.join([
            '| Rank | Model | Elo Score |',
            '|---|---|---|',
        ] + arena_rows)
        
        # ─── PyPI table ──────────────────────────────────────────────
        pypi_rows = [f'| `{p["package"]}` | {fmt_num(p["downloads_last_day"])} | {fmt_num(p["downloads_last_week"])} |'
                     for p in pypi[:8]]
        pypi_table = '\n'.join([
            '| Package | Daily Downloads | Weekly Downloads |',
            '|---|---|---|',
        ] + pypi_rows)
        
        # ─── Breakout model ──────────────────────────────────────────
        breakout = hf[0] if hf else {}
        breakout_line = f"`{breakout.get('id','—')}` — {fmt_num(breakout.get('downloads',0))} downloads" if breakout else 'No breakout model found.'
        
        readme = f'''# 🤖 Daily AI Tracker
        
> Auto-updated every 24 hours by GitHub Actions. Last run: **{date}**

[![Update](https://github.com/adityapichikala/Auto-llm-Scores/actions/workflows/update.yml/badge.svg)](https://github.com/adityapichikala/Auto-llm-Scores/actions)  
[![Dashboard](https://img.shields.io/badge/Live_Dashboard-View-blue)](https://adityapichikala.github.io/Auto-llm-Scores)

## 🔥 Breakout Model 
{breakout_line}

## ⚡ GitHub Velocity (24h Star Change)
{repo_table}

## 🏆 LMSYS Chatbot Arena
{arena_table}

## 📦 PyPI Daily Downloads
{pypi_table}

---
*Data sources: GitHub API · HuggingFace API · pypistats.org · LMSYS Arena*  
*[View interactive dashboard](https://adityapichikala.github.io/Auto-llm-Scores) · [Raw data](data/latest.json)*
'''
        Path('README.md').write_text(readme.strip() + '\n', encoding='utf-8')
        print('README.md updated.')
        
    except Exception as e:
        print(f"Error updating README: {e}")

if __name__ == '__main__':
    main()
