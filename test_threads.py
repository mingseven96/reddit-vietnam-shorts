import requests
import re

def test_scrape(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    r = requests.get(url, headers=headers)
    print("SIZE:", len(r.text))
    
    desc_match = re.search(r'<meta property="og:description" content="(.*?)"', r.text)
    title_match = re.search(r'<meta property="og:title" content="(.*?)"', r.text)
    
    title = title_match.group(1) if title_match else "N/A"
    desc = desc_match.group(1) if desc_match else "N/A"
    
    # decode html entities
    import html
    title = html.unescape(title)
    desc = html.unescape(desc)
    
    print(f"TITLE: {title}")
    print(f"DESC: {desc}")

if __name__ == "__main__":
    test_scrape("https://www.threads.net/@zuck/post/CuW6-7KyXOW")
