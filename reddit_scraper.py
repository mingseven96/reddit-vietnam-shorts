"""
reddit_scraper.py - Cào bài đăng trending từ Reddit
Hỗ trợ 2 phương thức:
  1. PRAW (Reddit official API - khuyến nghị, cần client_id/secret)
  2. Fallback: requests qua old.reddit.com JSON
"""

import sys
import io
import time
import random
import json
import re
from typing import Optional

# Fix Unicode encoding cho Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from config import (
    SUBREDDITS, POSTS_PER_SUBREDDIT, MIN_POST_WORDS,
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
)


# ─── Phương thức 1: PRAW (Reddit Official API) ─────────────────────────────

def fetch_with_praw(subreddit: str, limit: int = 10) -> list[dict]:
    """Cào bài đăng dùng PRAW (cần Reddit API credentials)."""
    try:
        import praw
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )

        sub = reddit.subreddit(subreddit)
        results = []

        for post in sub.hot(limit=limit * 3):
            if post.stickied or not post.selftext:
                continue

            text = post.selftext.strip()
            word_count = len(text.split())

            if word_count < MIN_POST_WORDS or text in ("[deleted]", "[removed]"):
                continue

            results.append({
                "id": post.id,
                "subreddit": subreddit,
                "title": post.title,
                "text": text,
                "score": post.score,
                "num_comments": post.num_comments,
                "url": f"https://reddit.com{post.permalink}",
                "word_count": word_count,
            })

            if len(results) >= limit:
                break

        return results

    except Exception as e:
        raise RuntimeError(f"PRAW error: {e}")


# ─── Phương thức 2: requests với nhiều User-Agent rotate ──────────────────

USER_AGENTS = [
    "RedditBot/1.0 by u/anonymous_scraper_bot",
    "python-praw/7.7.1 prawcore/2.3.0",
    "Mozilla/5.0 (compatible; RedditScraper/1.0)",
]


def fetch_with_requests(subreddit: str, limit: int = 10) -> list[dict]:
    """Cào bài đăng qua Reddit JSON API công khai."""
    import requests

    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
    })

    # Thử các endpoint khác nhau
    endpoints = [
        f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit * 3}&raw_json=1",
        f"https://old.reddit.com/r/{subreddit}/hot.json?limit={limit * 3}",
    ]

    for url in endpoints:
        try:
            time.sleep(random.uniform(1.0, 2.5))  # Rate limit delay
            response = session.get(url, timeout=20, allow_redirects=True)

            if response.status_code == 200:
                data = response.json()
                posts_raw = data.get("data", {}).get("children", [])
                results = []

                for post in posts_raw:
                    p = post["data"]
                    if p.get("stickied") or not p.get("selftext"):
                        continue

                    text = p["selftext"].strip()
                    word_count = len(text.split())

                    if word_count < MIN_POST_WORDS or text in ("[deleted]", "[removed]"):
                        continue

                    results.append({
                        "id": p["id"],
                        "subreddit": subreddit,
                        "title": p["title"],
                        "text": text,
                        "score": p.get("score", 0),
                        "num_comments": p.get("num_comments", 0),
                        "url": f"https://reddit.com{p['permalink']}",
                        "word_count": word_count,
                    })

                    if len(results) >= limit:
                        break

                if results:
                    return results

        except Exception as e:
            continue

    return []


# ─── Phương thức 3: Fallback thủ công (nếu Reddit block hoàn toàn) ─────────

DEMO_POSTS = [
    {
        "id": "demo1",
        "subreddit": "AmItheAsshole",
        "title": "AITA for telling my brother his wife was cheating on him before their wedding?",
        "text": """I (28F) found out my brother's (32M) fiancée was cheating on him with her coworker about two weeks before their wedding. I had solid proof - I accidentally saw their messages when she left her phone at my place.

I told my brother immediately. He was devastated. The wedding was called off, our whole family was in chaos.

Now my future sister-in-law's family is furious at me, saying I ruined everything and I should have stayed out of it. Some of them are saying I was jealous of my brother's happiness.

My brother is heartbroken but grateful I told him. He said he'd rather know now than find out later. But seeing how much pain everyone is in, I'm second-guessing myself.

Was I wrong to tell him? Should I have stayed out of it? AITA?""",
        "score": 45230,
        "num_comments": 3201,
        "url": "https://reddit.com/r/AmItheAsshole/demo1",
        "word_count": 148,
    },
    {
        "id": "demo2",
        "subreddit": "confessions",
        "title": "I've been pretending to go to work for 6 months. My family has no idea I was fired.",
        "text": """Six months ago I was fired from my job. I was too ashamed to tell my wife and kids. So every morning, I put on my suit, kiss my family goodbye, drive to the coffee shop and spend 8 hours job hunting, applying, doing freelance work online.

I've managed to keep the money situation relatively stable from savings and some freelance gigs. My wife thinks everything is fine.

I've had three interviews in the last week. One of them is looking really promising. I'm terrified she'll find out before I can fix this.

I know it was wrong. I know I should have told her from the start. I just couldn't face the disappointment in her eyes. She quit her job when we had kids because I promised I'd always provide.

If this next job comes through, maybe I'll never have to tell her. But the guilt is eating me alive.""",
        "score": 89450,
        "num_comments": 7823,
        "url": "https://reddit.com/r/confessions/demo2",
        "word_count": 166,
    },
    {
        "id": "demo3",
        "subreddit": "relationship_advice",
        "title": "Found out my husband of 10 years has a second family. We have 3 kids together.",
        "text": """I don't even know where to start. I've been married to my husband for 10 years. We have three kids (8, 6, and 4). Last Tuesday I found a receipt in his jacket pocket - a birthday cake, ordered for a child I don't know.

I did some digging (I know, I know). He has another woman. Another child. The other child is 5 years old. This has been going on for almost our entire marriage.

I confronted him last night. He broke down crying, said he loved both of us, that he never wanted to hurt anyone.

I'm staying at my sister's place right now with my kids. I have an appointment with a divorce lawyer tomorrow. But I'm still in shock. 10 years. Three kids. And he had a whole other family the entire time.

How do people even do this? How do I move forward?""",
        "score": 128900,
        "num_comments": 11204,
        "url": "https://reddit.com/r/relationship_advice/demo3",
        "word_count": 170,
    },
]


def fetch_hot_posts(subreddit: str, limit: int = 10) -> list[dict]:
    """
    Cào bài đăng hot từ subreddit. Tự động chọn phương thức phù hợp.
    Ưu tiên: PRAW > requests > Demo data
    """
    # Thử PRAW trước (nếu đã cấu hình)
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_ID != "YOUR_REDDIT_CLIENT_ID":
        try:
            return fetch_with_praw(subreddit, limit)
        except Exception:
            pass

    # Thử requests
    try:
        results = fetch_with_requests(subreddit, limit)
        if results:
            return results
    except Exception:
        pass

    return []


def fetch_all_trending_posts(verbose: bool = True) -> list[dict]:
    """
    Cào bài trending từ tất cả subreddit được cấu hình.
    Nếu không cào được từ Reddit, dùng demo data để test.
    """
    all_posts = []

    if verbose:
        print("[*] Dang tai du lieu tu Reddit...\n")

    for subreddit in SUBREDDITS:
        if verbose:
            print(f"  [->] Dang tai r/{subreddit}...", end=" ", flush=True)

        posts = fetch_hot_posts(subreddit, POSTS_PER_SUBREDDIT)

        if verbose:
            print(f"OK - Lay duoc {len(posts)} bai")

        all_posts.extend(posts)
        time.sleep(random.uniform(1.0, 2.0))

    # Nếu không lấy được gì -> dùng demo data
    if not all_posts:
        if verbose:
            print("\n[!] Khong ket noi duoc Reddit. Dang dung du lieu demo...\n")
        all_posts = DEMO_POSTS.copy()

    # Sắp xếp theo điểm số
    all_posts.sort(key=lambda x: x["score"], reverse=True)

    if verbose:
        print(f"\n[+] Tong cong: {len(all_posts)} bai dang\n")

    return all_posts


def display_posts_menu(posts: list[dict]) -> Optional[dict]:
    """Hiển thị danh sách bài đăng và để người dùng chọn."""
    if not posts:
        print("[!] Khong tim thay bai dang phu hop.")
        return None

    print(f"\n{'='*70}")
    print(f"  TIM THAY {len(posts)} BAI DANG DANG HOT TU REDDIT")
    print(f"{'='*70}\n")

    for i, post in enumerate(posts, 1):
        score_str = f"Up: {post['score']:,}"
        comment_str = f"Cmt: {post['num_comments']:,}"
        words_str = f"{post['word_count']} tu"
        subreddit_str = f"r/{post['subreddit']}"

        print(f"  [{i:2d}] {subreddit_str:<25} {score_str:<15} {comment_str:<12} {words_str}")
        safe_title = post['title'][:80].encode('ascii', errors='replace').decode('ascii')
        print(f"       >> {safe_title}{'...' if len(post['title']) > 80 else ''}")
        print()

    print(f"{'='*70}")
    print("   [0] Thoat")
    print(f"{'='*70}\n")

    while True:
        try:
            choice = input(">> Chon so thu tu bai ban muon lam video: ").strip()

            if choice == "0":
                print("Tam biet!")
                return None

            choice_int = int(choice)
            if 1 <= choice_int <= len(posts):
                selected = posts[choice_int - 1]
                safe_title = selected['title'][:60].encode('ascii', errors='replace').decode('ascii')
                print(f"\n[OK] Da chon bai #{choice_int}: {safe_title}...\n")
                return selected
            else:
                print(f"  [!] Vui long nhap so tu 0 den {len(posts)}")

        except ValueError:
            print("  [!] Vui long nhap mot so hop le")


if __name__ == "__main__":
    posts = fetch_all_trending_posts()
    selected = display_posts_menu(posts)
    if selected:
        print("\n--- NOI DUNG BAI DANG ---")
        safe_title = selected['title'].encode('ascii', errors='replace').decode('ascii')
        print(f"Tieu de: {safe_title}")
        print(f"Nguon: {selected['url']}")
        print(f"\nNoi dung (300 ky tu dau):\n{selected['text'][:300]}...")
