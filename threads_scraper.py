import requests
import re
import html

def fetch_thread_post(url: str) -> dict:
    """
    Cào bài viết từ Threads bằng URL
    """
    print(f"\n[*] Đang cào dữ liệu từ Threads: {url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        desc_match = re.search(r'<meta property="og:description" content="(.*?)"', r.text)
        title_match = re.search(r'<meta property="og:title" content="(.*?)"', r.text)
        
        author_raw = title_match.group(1) if title_match else "N/A"
        desc_raw = desc_match.group(1) if desc_match else "N/A"
        
        author = html.unescape(author_raw)
        text = html.unescape(desc_raw)
        
        # Bóc tách Username
        username = author.split("(@")[1].split(")")[0] if "(@" in author else author.split(" on Threads")[0]
        
        # Bóc tách lượt thích / comment nếu có trong description
        # Meta tag thường có format: "123 Likes, 45 Comments. nội dung..."
        score = "N/A"
        comments = "N/A"
        
        # Tách số liệu khỏi văn bản nếu có
        # VD: "1.2K Likes, 345 Comments. Chuyện là..."
        stats_match = re.match(r'^(.*? Likes, .*? Comments)\.\s*(.*)', text)
        if stats_match:
            stats = stats_match.group(1)
            text = stats_match.group(2)
            
            # Phân tích stats
            if "Likes" in stats:
                score = stats.split(" Likes")[0].strip()
            if "Comments" in stats:
                comments = stats.split(" Likes, ")[1].split(" Comments")[0].strip() if " Likes, " in stats else stats.split(" Comments")[0].strip()
        
        # Nếu url có dạng dài, lấy ID ngắn
        post_id = url.split("/post/")[1].split("/")[0] if "/post/" in url else "thread"
        
        return {
            "id": post_id,
            "author": username,
            "title": f"Bài viết từ @{username}",
            "text": text,
            "url": url,
            "score": score,
            "num_comments": comments,
            "subreddit": "threads"
        }
        
    except Exception as e:
        print(f"[!] Lỗi khi lấy bài Threads: {e}")
        return None
