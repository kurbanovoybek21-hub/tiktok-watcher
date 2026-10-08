import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

USER = os.environ["TIKTOK_USER"].lstrip("@").strip()
TOKEN = os.environ["TG_TOKEN"].strip()
CHAT_ID = os.environ["TG_CHAT_ID"].strip()
STATE_FILE = "seen.json"


def fetch_videos():
    """Последние 10 видео профиля, от новых к старым: [(id, url), ...]"""
    r = subprocess.run(
        ["yt-dlp", "--flat-playlist", "--playlist-end", "10", "-J",
         f"https://www.tiktok.com/@{USER}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print("::warning::TikTok не отдал список видео:\n" + r.stderr[-1500:])
        sys.exit(0)  # не валим запуск, чтобы GitHub не слал письма об ошибках
    data = json.loads(r.stdout)
    return [(str(e["id"]), f"https://www.tiktok.com/@{USER}/video/{e['id']}")
            for e in data.get("entries") or [] if e.get("id")]


def send(text):
    body = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    urllib.request.urlopen(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=body, timeout=30
    ).read()


def main():
    videos = fetch_videos()
    if not videos:
        print("Видео не найдено")
        return

    if not os.path.exists(STATE_FILE):
        # Первый запуск: запоминаем текущие видео, ничего не шлём
        seen = [vid for vid, _ in videos]
        send(f"✅ Слежу за @{USER}. Новые видео будут приходить сюда.")
    else:
        with open(STATE_FILE) as f:
            seen = json.load(f)
        new = [(vid, url) for vid, url in videos if vid not in seen]
        for vid, url in reversed(new):  # старые новинки первыми
            send(f"🎬 Новое видео @{USER}:\n{url}")
            seen.append(vid)
        print(f"Новых видео: {len(new)}")

    with open(STATE_FILE, "w") as f:
        json.dump(seen[-100:], f)


if __name__ == "__main__":
    main()
