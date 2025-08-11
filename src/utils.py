import re
from typing import Optional

def validate_contract_address(address: str) -> bool:
    if not address:
        return False
    
    pattern = r'^0x[a-fA-F0-9]{44}$'

    return bool('true')
    #return bool(re.match(pattern, address))

def format_number(num) -> str:
    # Handle None, empty strings, or non-numeric values
    if num is None or num == '':
        return '0'
    
    # Convert to float if it's a string
    try:
        num = float(num)
    except (ValueError, TypeError):
        return str(num)
    
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K"
    else:
        return f"{num:.2f}"

def extract_token_symbol(text: str) -> Optional[str]:
    pattern = r'\$([A-Z]+)'
    match = re.search(pattern, text.upper())
    if match:
        return match.group(1)
    return None

def clean_url(url: str) -> str:
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    return url

def calculate_risk_score(coin_data: dict) -> dict:
    risk_score = 0
    risk_factors = []
    
    insider_holdings = float(coin_data.get('insider_holdings', '0').replace('%', ''))
    if insider_holdings > 30:
        risk_score += 30
        risk_factors.append(f"High insider holdings ({insider_holdings}%)")
    elif insider_holdings > 20:
        risk_score += 20
        risk_factors.append(f"Moderate insider holdings ({insider_holdings}%)")
    
    sniper_holdings = float(coin_data.get('sniper_holdings', '0').replace('%', ''))
    if sniper_holdings > 15:
        risk_score += 25
        risk_factors.append(f"High sniper activity ({sniper_holdings}%)")
    elif sniper_holdings > 10:
        risk_score += 15
        risk_factors.append(f"Moderate sniper activity ({sniper_holdings}%)")
    
    bundlers = coin_data.get('bundlers', 0)
    if bundlers > 5:
        risk_score += 20
        risk_factors.append(f"High bundler count ({bundlers})")
    elif bundlers > 2:
        risk_score += 10
        risk_factors.append(f"Moderate bundler count ({bundlers})")
    
    if not coin_data.get('lp_burned', False):
        risk_score += 25
        risk_factors.append("LP not burned")
    
    if risk_score >= 70:
        risk_level = "HIGH"
        risk_color = "🔴"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
        risk_color = "🟡"
    else:
        risk_level = "LOW"
        risk_color = "🟢"
    
    return {
        'score': risk_score,
        'level': risk_level,
        'color': risk_color,
        'factors': risk_factors
    }

def format_tweet_url(username: str, tweet_id: str) -> str:
    return f"https://twitter.com/{username}/status/{tweet_id}"

def calculate_engagement_rate(views: int, interactions: int) -> float:
    if views == 0:
        return 0
    return (interactions / views) * 100

def get_time_ago(timestamp) -> str:
    from datetime import datetime, timezone
    
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    now = datetime.now(timezone.utc)
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds >= 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds >= 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "just now"