import os, json, requests, datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WEBHOOK = os.environ.get('DISCORD_WEBHOOK_URL', '')

def fmt(n):
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M'
    if n >= 1_000:     return f'{n/1_000:.1f}k'
    return str(n)

def main():
    if not WEBHOOK:
        print('No webhook URL — skipping Discord alert.')
        return
        
    latest_path = Path('data/latest.json')
    if not latest_path.exists():
        print('No latest.json found.')
        return
        
    try:
        data  = json.loads(latest_path.read_text(encoding='utf-8'))
        repos = data.get('repos', [])[:3]
        arena = data.get('lmsys_arena', [])[:3]
        hf    = data.get('hf_trending', [{}])[0] if data.get('hf_trending') else {}
        pypi  = data.get('pypi', [{}])[0] if data.get('pypi') else {}
        
        # Build the embed
        repo_lines = '\n'.join(
            f"`{r['repo'].split('/')[-1]}` — ⭐{fmt(r['stars'])}  🔥+{fmt(r['delta_24h'])}"
            for r in repos
        ) if repos else "No data"
        
        arena_lines = '\n'.join(
            f"`#{a['rank']}` {a['model']} — Elo {a['elo']}" for a in arena
        ) if arena else "No data"
        
        embed = {
            'title': f'🤖 Daily AI Pulse — {data.get("date", "Unknown Date")}',
            'color': 0x2563EB,
            'fields': [
                {'name': '⚡ Top Velocity Repos', 'value': repo_lines, 'inline': False},
                {'name': '🏆 Arena Top 3', 'value': arena_lines, 'inline': False},
                {'name': '🔥 Breakout Model', 'value': hf.get('id', '—'), 'inline': True},
                {'name': '📦 Top Library', 'value': f"`{pypi.get('package','—')}` {fmt(pypi.get('downloads_last_day',0))}/day", 'inline': True},
            ],
            'footer': {'text': 'View full dashboard → YOUR_USERNAME.github.io/ai-tracker'},
            'timestamp': datetime.datetime.utcnow().isoformat(),
        }
        
        r = requests.post(WEBHOOK, json={'embeds': [embed]}, timeout=10)
        print(f'Discord Webhook Status: {r.status_code}')
    except Exception as e:
        print(f"Failed to send Discord alert: {e}")

if __name__ == '__main__':
    main()
