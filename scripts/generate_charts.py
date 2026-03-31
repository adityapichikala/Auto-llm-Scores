import json, csv, datetime
import matplotlib
matplotlib.use('Agg')      # Non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

CHARTS_DIR = Path('charts')
CHARTS_DIR.mkdir(exist_ok=True)

def load_history(days=14):
    snap_dir = Path('data/snapshots')
    if not snap_dir.exists():
        return defaultdict(list)
    
    # Get last N days of snapshots
    snap_files = sorted(snap_dir.glob('*.json'))[-days:]
    
    by_repo = defaultdict(list)
    for snap_file in snap_files:
        try:
            data = json.loads(snap_file.read_text(encoding='utf-8'))
            for repo in data.get('repos', []):
                # We want a series of stars over time
                by_repo[repo['repo']].append(repo['stars'])
        except Exception as e:
            print(f"Warning: Error loading {snap_file.name}: {e}")
            
    return by_repo

def sparkline(values, filename, color='#2563EB', hot_color='#EA580C'):
    """Generates a small, clean sparkline chart."""
    if not values or len(values) < 2:
        return

    fig, ax = plt.subplots(figsize=(2.0, 0.6))  # Slightly larger for quality
    fig.patch.set_alpha(0)
    ax.set_facecolor('none')
    
    # Use hot color if trending up significantly (last value > 1% above average of previous)
    avg_prev = sum(values[:-1]) / len(values[:-1]) if len(values) > 1 else values[0]
    c = hot_color if values[-1] > avg_prev * 1.01 else color
    
    ax.plot(values, color=c, linewidth=2.5, solid_capstyle='round')
    ax.fill_between(range(len(values)), values, min(values),
                    alpha=0.1, color=c)
    ax.axis('off')
    
    # Padding and limits
    vmin, vmax = min(values), max(values)
    if vmin == vmax:
        ax.set_ylim(vmin - 1, vmax + 1)
    else:
        ax.set_ylim(vmin - (vmax-vmin)*0.1, vmax + (vmax-vmin)*0.1)
        
    plt.tight_layout(pad=0)
    plt.savefig(CHARTS_DIR / filename, dpi=120, bbox_inches='tight', transparent=True)
    plt.close()

def main():
    print("Generating sparkline charts...")
    history = load_history(14)
    if not history:
        print("No historical data found in data/snapshots/.")
        return
        
    count = 0
    for repo, star_series in history.items():
        if len(star_series) < 2:
            continue
            
        safe_name = repo.replace('/', '_')
        sparkline(star_series, f'{safe_name}_spark.png')
        count += 1
        
    print(f'Generated {count} sparkline charts.')

if __name__ == '__main__':
    main()
