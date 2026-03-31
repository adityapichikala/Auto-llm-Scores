import os, json, csv, requests, datetime, time
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

TODAY     = datetime.date.today().isoformat()
YESTERDAY = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

DATA_DIR  = Path('data')
SNAP_DIR  = DATA_DIR / 'snapshots'
SNAP_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_TOKEN = os.environ.get('GH_TOKEN', os.environ.get('GITHUB_TOKEN', ''))
HF_TOKEN     = os.environ.get('HF_TOKEN', '')

def get_session():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

session = get_session()

GH_HEADERS = {
    'Authorization': f'Bearer {GITHUB_TOKEN}' if GITHUB_TOKEN else '',
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
}
if not GH_HEADERS['Authorization']: del GH_HEADERS['Authorization']

TRACKED_REPOS = [
    'vllm-project/vllm',
    'huggingface/transformers',
    'langchain-ai/langchain',
    'openai/openai-python',
    'unslothai/unsloth',
    'microsoft/Phi-4',
    'deepseek-ai/DeepSeek-V3',
    'ggerganov/llama.cpp',
    'BerriAI/litellm',
    'ollama/ollama',
]

def fetch_github_repos():
    results = []
    yesterday_snap = SNAP_DIR / f'{YESTERDAY}.json'
    prev = {}
    if yesterday_snap.exists():
        try:
            prev_data = json.loads(yesterday_snap.read_text())
            prev = {r['repo']: r['stars'] for r in prev_data.get('repos', [])}
        except Exception as e:
            print(f"Warning: Could not parse yesterday's snapshot: {e}")

    for repo in TRACKED_REPOS:
        try:
            url = f'https://api.github.com/repos/{repo}'
            r = session.get(url, headers=GH_HEADERS, timeout=15)
            r.raise_for_status()
            
            data = r.json()
            stars = data['stargazers_count']
            delta = stars - prev.get(repo, stars)
            results.append({
                'repo': repo,
                'stars': stars,
                'delta_24h': delta,
                'forks': data['forks_count'],
                'open_issues': data['open_issues_count'],
                'language': data.get('language', ''),
                'description': (data.get('description') or '')[:120],
            })
        except Exception as e:
            print(f'Failed to fetch GitHub repo {repo}: {e}')
            
    results.sort(key=lambda x: x['delta_24h'], reverse=True)
    return results

def fetch_hf_trending():
    try:
        url = 'https://huggingface.co/api/trending'
        headers = {'Authorization': f'Bearer {HF_TOKEN}'} if HF_TOKEN else {}
        r = session.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        trending = data.get('recentlyTrending', [])
        # Filter to models only
        models = [item for item in trending if item.get('repoType') == 'model']
        return [{
            'id': m.get('repoData', {}).get('id', ''),
            'downloads': m.get('repoData', {}).get('downloads', 0),
            'likes': m.get('repoData', {}).get('likes', 0),
            'pipeline_tag': m.get('repoData', {}).get('pipeline_tag', ''),
        } for m in models[:10]]
    except Exception as e:
        print(f'Failed to fetch HF trending models: {e}')
        return []

def fetch_pypi_downloads():
    packages = ['transformers', 'openai', 'langchain', 'vllm', 'anthropic',
                'llama-index', 'sentence-transformers', 'accelerate']
    results = []
    for pkg in packages:
        try:
            url = f'https://pypistats.org/api/packages/{pkg}/recent'
            r = session.get(url, timeout=15)
            r.raise_for_status()
            data = r.json().get('data', {})
            results.append({
                'package': pkg,
                'downloads_last_day': data.get('last_day', 0),
                'downloads_last_week': data.get('last_week', 0),
                'downloads_last_month': data.get('last_month', 0),
            })
            time.sleep(1)
        except Exception as e:
            print(f'Failed to fetch PyPI stats for {pkg}: {e}')
    results.sort(key=lambda x: x['downloads_last_day'], reverse=True)
    return results

def fetch_lmsys_arena():
    """Fetch LMSYS arena data from their HuggingFace space API."""
    try:
        # Try the Gradio API endpoint for the leaderboard space
        url = 'https://lmarena.ai/api/v1/leaderboard'
        r = session.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        results = []
        for i, entry in enumerate(data[:10]):
            results.append({
                'rank': i + 1,
                'model': entry.get('name', entry.get('model', 'Unknown')),
                'elo': str(entry.get('score', entry.get('elo', '—'))),
            })
        return results
    except Exception:
        # Fallback: use the HF models API to get top chat models by likes as a proxy
        try:
            url = 'https://huggingface.co/api/models?pipeline_tag=text-generation&sort=likes&direction=-1&limit=10'
            headers = {'Authorization': f'Bearer {HF_TOKEN}'} if HF_TOKEN else {}
            r = session.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            models = r.json()
            return [{
                'rank': i + 1,
                'model': m.get('id', 'Unknown'),
                'elo': f"{m.get('likes', 0):,} likes",
            } for i, m in enumerate(models[:10])]
        except Exception as e:
            print(f'LMSYS/HF fallback failed: {e}')
            return []


def main():
    print(f'Fetching daily AI pulse data for {TODAY}...')
    
    payload = {
        'date': TODAY,
        'repos': fetch_github_repos(),
        'hf_trending': fetch_hf_trending(),
        'pypi': fetch_pypi_downloads(),
        'lmsys_arena': fetch_lmsys_arena(),
    }
    
    # Save snapshots
    (SNAP_DIR / f'{TODAY}.json').write_text(json.dumps(payload, indent=2))
    (DATA_DIR / 'latest.json').write_text(json.dumps(payload, indent=2))
    
    # Web dashboard data
    web_dir = Path('web')
    web_dir.mkdir(exist_ok=True)
    (web_dir / 'data.json').write_text(json.dumps(payload, indent=2))
    
    # Historical CSV
    csv_path = DATA_DIR / 'historical.csv'
    write_header = not csv_path.exists()
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(['date', 'repo', 'stars', 'delta_24h'])
        for repo in payload.get('repos', []):
            writer.writerow([TODAY, repo['repo'], repo['stars'], repo['delta_24h']])
            
    print(f'Successfully saved data for {TODAY}.')

if __name__ == '__main__':
    main()
