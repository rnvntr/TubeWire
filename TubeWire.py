import time
import feedparser
import requests
import json
import os
from datetime import datetime, timedelta, timezone

# ----------------------------------
# TubeWire Script Metadata
# ----------------------------------
SCRIPT_NAME = "TubeWire"
AUTHOR_NAME = "rnvntr"
VERSION = "1.0.0"

# ----------------------------------
# Configuration
# ----------------------------------
CHANNEL_ID = "" # Find your YouTube user & channel IDs (https://support.google.com/youtube/answer/3250431?hl=en)
DISCORD_WEBHOOK_URL = "" # Intro to Webhooks (https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)
CHECK_INTERVAL = 300  # seconds between checks (5 minutes)

# Notification customization
DISCORD_BOT_NAME = ""  # If empty, Discord uses the webhook's default name
DISCORD_BOT_ICON = ""  # If empty, Discord uses the webhook's default avatar

# If you want to mention @everyone or add extra text at the top-level content, set this
MENTION_TEXT = ""

# Max age in hours that a newly found video can have to trigger a notification
MAX_VIDEO_AGE_HOURS = 24

# Notification style: "LINK_ONLY", "CUSTOM_EMBED", or "HYBRID"
NOTIFICATION_STYLE = "LINK_ONLY"

# For the custom embed style or hybrid, pick a color (0xRRGGBB)
EMBED_COLOR = 0xFF5733

# Where we store the last-notified video ID
# (Renamed to include "TubeWire" at the beginning)
STORAGE_FILE = "TubeWire_last_video_id.json"


def load_last_video_id():
    """Load the stored video ID from a file (if it exists)."""
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("last_video_id", None)
    return None


def save_last_video_id(video_id):
    """Save the latest video ID to a file."""
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_video_id": video_id}, f)


def get_latest_video(channel_id):
    """
    Parse the YouTube channel's Atom feed and return the latest video info as a dict:
    {
        'id': 'VIDEO_ID',
        'title': 'Video Title',
        'url': 'https://youtu.be/VIDEO_ID',
        'published': 'YYYY-MM-DDTHH:MM:SSZ',
        'published_parsed': time.struct_time
    }
    Returns None if feed is empty or inaccessible.
    """
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        return None
    
    latest_entry = feed.entries[0]
    
    video_id = latest_entry.yt_videoid
    video_title = latest_entry.title
    video_link = latest_entry.link
    
    published_text = getattr(latest_entry, 'published', None)
    published_parsed = getattr(latest_entry, 'published_parsed', None)

    return {
        "id": video_id,
        "title": video_title,
        "url": video_link,
        "published": published_text,
        "published_parsed": published_parsed
    }


def is_within_max_age(video):
    """Check if the video's publish time is within MAX_VIDEO_AGE_HOURS."""
    if video["published_parsed"] is None:
        print("[WARN] No parsed date in feed. Skipping age check.")
        return True  # or False if you prefer

    published_naive = datetime.fromtimestamp(time.mktime(video["published_parsed"]))
    published_dt = published_naive.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    video_age = now - published_dt
    
    if video_age.total_seconds() < 0:
        video_age = timedelta(seconds=0)
    
    hours_old = video_age.total_seconds() / 3600
    return hours_old <= MAX_VIDEO_AGE_HOURS


def build_discord_payload(video):
    """
    Based on NOTIFICATION_STYLE, build the JSON payload for Discord.
    Returns a dict that can be passed to requests.post(..., json=payload).
    """
    title = video["title"]
    url = video["url"]
    published = video["published"]

    if NOTIFICATION_STYLE == "LINK_ONLY":
        # Plain text content with YouTube link — Discord typically shows the big preview
        content_text = f"{MENTION_TEXT} {title} {url}".strip()
        payload = {"content": content_text}

    elif NOTIFICATION_STYLE == "CUSTOM_EMBED":
        # Fully custom embed, likely overrides the native YouTube preview
        embed = {
            "title": title,
            "url": url,
            "description": f"Published: {published}",
            "color": EMBED_COLOR,
        }
        # embed["thumbnail"] = {"url": f"https://img.youtube.com/vi/{video['id']}/maxresdefault.jpg"}

        payload = {
            "embeds": [embed]
        }
        if MENTION_TEXT:
            payload["content"] = MENTION_TEXT

    elif NOTIFICATION_STYLE == "HYBRID":
        # Attempt both a direct link in 'content' and a custom embed
        content_text = f"{MENTION_TEXT} {url}".strip()
        embed = {
            "title": title,
            "description": f"Published: {published}",
            "color": EMBED_COLOR,
        }
        # embed["thumbnail"] = {"url": f"https://img.youtube.com/vi/{video['id']}/maxresdefault.jpg"}

        payload = {
            "content": content_text,
            "embeds": [embed]
        }

    else:
        # Fallback if someone puts an invalid style
        print(f"[WARN] Unsupported NOTIFICATION_STYLE: {NOTIFICATION_STYLE}. Using LINK_ONLY.")
        content_text = f"{MENTION_TEXT} {title} {url}".strip()
        payload = {"content": content_text}

    # Add username/avatar only if non-empty
    if DISCORD_BOT_NAME:
        payload["username"] = DISCORD_BOT_NAME
    if DISCORD_BOT_ICON:
        payload["avatar_url"] = DISCORD_BOT_ICON

    return payload


def post_to_discord(payload, video_title):
    """Send the prepared payload to Discord."""
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"[INFO] Posted new video to Discord: {video_title}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to post to Discord: {e}")


def main():
    print(f"[INFO] {SCRIPT_NAME} v{VERSION} by {AUTHOR_NAME} started.")
    print(f"[INFO] NOTIFICATION_STYLE = {NOTIFICATION_STYLE}")

    last_video_id = load_last_video_id()

    while True:
        latest_video = get_latest_video(CHANNEL_ID)
        if latest_video is None:
            print("[WARN] Could not retrieve the feed or feed is empty. Retrying...")
        else:
            if latest_video["id"] != last_video_id:
                if is_within_max_age(latest_video):
                    payload = build_discord_payload(latest_video)
                    post_to_discord(payload, latest_video["title"])

                    save_last_video_id(latest_video["id"])
                    last_video_id = latest_video["id"]
                else:
                    print(f"[INFO] Found new video: {latest_video['title']} "
                          f"but it’s older than {MAX_VIDEO_AGE_HOURS} hour(s). Skipping.")
            else:
                print(f"[INFO] No new video. Latest is still: {latest_video['title']}")
        
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
