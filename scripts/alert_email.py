import os, json
import resend
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuration
resend.api_key = os.environ.get('RESEND_API_KEY', '')
FROM_EMAIL = "tracker@yourdomain.com"
TO_EMAIL = os.environ.get('DIGEST_EMAIL_TO', '')

def build_html(data):
    date = data.get('date', 'Unknown Date')
    repos = data.get('repos', [])[:5]
    
    rows = ""
    for r in repos:
        delta = r.get("delta_24h", 0)
        color = "#10b981" if delta > 0 else "#64748b"
        rows += f"""
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px; font-weight: 500;">{r['repo']}</td>
            <td style="padding: 12px;">{r['stars']:,}</td>
            <td style="padding: 12px; color: {color}; font-weight: bold;">
                {'+' if delta > 0 else ''}{delta:,}
            </td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family: -apple-system, sans-serif; background: #f8fafc; color: #1e293b; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="background: #1e3a8a; color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">🚀 Weekly AI Pulse</h1>
                <p style="margin: 10px 0 0; opacity: 0.8;">Insightful summary for {date}</p>
            </div>
            <div style="padding: 30px;">
                <h2 style="font-size: 18px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px;">⚡ Top Trending Repositories</h2>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="text-align: left; background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                            <th style="padding: 12px;">Repo</th>
                            <th style="padding: 12px;">Stars</th>
                            <th style="padding: 12px;">24h Change</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; text-align: center;">
                    <a href="https://github.com/adityapichikala/ai-tracker" 
                       style="background: #2563eb; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600;">
                       View Full Dashboard
                    </a>
                </div>
            </div>
            <div style="background: #f1f5f9; padding: 20px; text-align: center; font-size: 12px; color: #64748b;">
                You are receiving this because you subscribed to the AI Tracker weekly digest.<br>
                GitHub: adityapichikala
            </div>
        </div>
    </body>
    </html>
    """

def main():
    if not resend.api_key or not TO_EMAIL:
        print("Error: Missing RESEND_API_KEY or DIGEST_EMAIL_TO. Check your secrets.")
        return

    latest_path = Path('data/latest.json')
    if not latest_path.exists():
        print("Error: data/latest.json not found. Run fetch.py first.")
        return
        
    try:
        data = json.loads(latest_path.read_text(encoding='utf-8'))
        subject = f"Weekly AI Pulse Digest — {data.get('date', 'Latest')}"
        html_content = build_html(data)
        
        params = {
            "from": f"AI Tracker <{FROM_EMAIL}>",
            "to": [TO_EMAIL],
            "subject": subject,
            "html": html_content,
        }
        
        email = resend.Emails.send(params)
        print(f"Weekly Digest sent successfully! ID: {email.get('id', 'unknown')}")
        
    except Exception as e:
        print(f"Failed to send email via Resend: {e}")

if __name__ == '__main__':
    main()
