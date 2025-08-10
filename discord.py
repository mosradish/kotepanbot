# discord.py
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_embed(tweet, target_username):
    embed = {
        "username": "Twitter通知Bot",
        "avatar_url": "https://abs.twimg.com/icons/apple-touch-icon-192x192.png",
        "embeds": [
            {
                "title": f"📢 @{tweet.get('author_username', target_username)} さんの新しいツイート",
                "url": f"https://twitter.com/{tweet.get('author_username', target_username)}/status/{tweet['id']}",
                "description": tweet.get("text", "")[:2048],
                "color": 0x1DA1F2,
                "footer": {
                    "text": "Twitter → Discord 自動通知"
                },
                "timestamp": tweet.get("created_at")
            }
        ]
    }
    headers = {"Content-Type": "application/json"}
    resp = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(embed), headers=headers)
    resp.raise_for_status()
