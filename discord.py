import os
import json
import requests

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_discord_embed(tweet, target_username):
    author = tweet.get("author_username", target_username)
    tweet_text = tweet.get("text", "")
    if len(tweet_text) > 400:
        tweet_text = tweet_text[:397] + "..."

    embed = {
        "embeds": [
            {
                "title": f"📢 @{author} さんの新しいツイート",
                "url": f"https://twitter.com/{author}/status/{tweet['id']}",
                "description": tweet_text,
                "color": 0x1DA1F2,
                "footer": {
                    "text": "Twitter → Discord 自動通知"
                },
                "timestamp": tweet.get("created_at"),
                "fields": [
                    {
                        "name": "投稿日時",
                        "value": tweet.get("created_at"),
                        "inline": True
                    },
                    {
                        "name": "ツイートID",
                        "value": tweet["id"],
                        "inline": True
                    }
                ],
            }
        ]
    }

    # 画像がある場合は追加
    media_url = tweet.get("media_url")
    if media_url:
        embed["embeds"][0]["image"] = {"url": media_url}

    headers = {"Content-Type": "application/json"}
    resp = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(embed), headers=headers)
    resp.raise_for_status()
