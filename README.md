# TubeWire

A Python script that checks your YouTube channel's Atom feed for new videos and posts notifications to a Discord channel via Webhook.

## Features

- Monitors a YouTube channel for new uploads  
- Posts a Discord message with either:
  - A **plain link** (to get Discord's native YouTube preview)
  - A **custom embed** (fully controlled layout)
  - A **hybrid** approach (attempting both)
- Respects an adjustable **max age** for new videos (skip old uploads)
- Configurable check interval
- Optionally mention `@everyone` or set a custom bot name/avatar

## Requirements

- Python 3.7+ (tested up to 3.11)
- `feedparser` and `requests` libraries

Install them:
```bash
pip install feedparser requests
```

## Configuration

Inside `TubeWire.py`, update these variables as desired:

- `CHANNEL_ID` — The YouTube channel ID you want to monitor.
- `DISCORD_WEBHOOK_URL` — Your Discord webhook URL.
- `NOTIFICATION_STYLE` — Options: `LINK_ONLY`, `CUSTOM_EMBED`, or `HYBRID`.
- `CHECK_INTERVAL` — Time in seconds between feed checks (e.g., 300 = 5 minutes).
- `MAX_VIDEO_AGE_HOURS` — Skip posting if a video is older than this threshold.
- `DISCORD_BOT_NAME` / `DISCORD_BOT_ICON` — Override the webhook's name/icon.
- `MENTION_TEXT` — Set to `@everyone` or any extra text. If blank, no mention is included.

## How to Run

```bash
python TubeWire.py
```

You should see console output such as:
```
[INFO] TubeWire v1.0.0 by Your Name Here started.
[INFO] NOTIFICATION_STYLE = LINK_ONLY
[INFO] No new video. Latest is still: ...
```

Leave it running if you want constant monitoring, or set up a cron job / scheduled task to run periodically.

## Troubleshooting

1. **ModuleNotFoundError**: Make sure you installed `feedparser` and `requests`.
2. **No feed entries**: Double-check `CHANNEL_ID`. Paste your feed URL into a browser: `https://www.youtube.com/feeds/videos.xml?channel_id=XXXX`.
3. **400 Bad Request** from Discord: Ensure your JSON payload isn't empty. If `NOTIFICATION_STYLE = LINK_ONLY`, you must pass a non-empty message in `content`.
4. **Doesn't post**: It might have already posted. Delete `TubeWire_last_video_id.json` to reset tracking or wait for a genuinely new video.

## Contributing

Feel free to fork, submit pull requests, or open issues with suggestions!
