"""
translator.py - Tóm tắt và viết lại drama từ Threads sang dạng kịch bản Tiktok giật gân.
Sử dụng OpenAI SDK (kết nối OpenRouter) để tạo kịch bản viral.
"""

import sys
import io
import re
import json
import math
from openai import OpenAI

# Fix Unicode encoding cho Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    TARGET_VIDEO_DURATION_SECONDS, WORDS_PER_MINUTE
)


def setup_gemini():
    """Khởi tạo OpenAI API client kết nối tới OpenRouter."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=GEMINI_API_KEY,
    )
    return client


def calculate_target_word_count() -> int:
    """Tính số từ mục tiêu dựa trên thời lượng video và tốc độ đọc."""
    return math.floor((TARGET_VIDEO_DURATION_SECONDS / 60) * WORDS_PER_MINUTE)


def translate_and_dramatize(post: dict, client) -> dict:
    """
    Chuyển thể câu chuyện Reddit tiếng Anh thành hội thoại tin nhắn giả lập (Fake Chat) tiếng Việt.

    Args:
        post: Dict chứa thông tin bài đăng Reddit
        client: OpenAI client kết nối qua OpenRouter

    Returns:
        Dict chứa: title_vi, hashtags, messages
    """
    target_words = calculate_target_word_count()

    prompt = f"""Bạn là biên kịch chuyên nghiệp cho video TikTok "Fake Chat Story".
Nhiệm vụ của bạn là đọc câu chuyện từ Reddit (tiếng Anh) và chuyển hóa nó thành một đoạn chat gay cấn giữa 2 nhân vật (Zalo hoặc Messenger) bằng tiếng Việt Gen Z.

--- THÔNG TIN BÀI GỐC ---
Subreddit: r/{post.get('subreddit', 'story')}
Tiêu đề: {post.get('title', 'Câu chuyện giật gân')}

Nội dung:
{post.get('text', '')[:3000]}
--- KẾT THÚC BÀI GỐC ---

--- YÊU CẦU CHO KỊCH BẢN CHAT ---
1. TỔNG SỐ TỪ CỦA CÁC TIN NHẮN PHẢI CHÍNH XÁC KHOẢNG {target_words} TỪ (đọc trong khoảng {TARGET_VIDEO_DURATION_SECONDS} giây).
2. HAI NHÂN VẬT: Hãy tự đặt tên cho 2 người (ví dụ: Chồng/Vợ, Mẹ chồng/Nàng dâu, Sếp/Nhân viên, Trà xanh/Chính thất). Một người là Nam, một người là Nữ để phân biệt giọng đọc.
3. KỊCH TÍNH NGAY LẬP TỨC: Tin nhắn đầu tiên phải đánh thẳng vào trọng tâm cực gắt (VD: "Anh gửi lộn ảnh cô ta cho em rồi kìa", "Tại sao mẹ lại vứt đồ của con?"). KHÔNG cần chào hỏi rườm rà.
4. NGÔN TỪ: Văn phong chat Zalo/Messenger của người Việt, có dùng từ lóng, viết tắt nhẹ, phẫn nộ, cảm xúc.

ĐỊNH DẠNG ĐẦU RA (Output Format):
Bạn CHỈ ĐƯỢC PHÉP trả về dữ liệu định dạng JSON hợp lệ, với cấu trúc sau:
{{
    "title_vi": "Tiêu đề tiếng Việt ngắn gọn, giật tít, tối đa 12 chữ",
    "hashtags": "#drama #phốt #xuhuong #redditvn",
    "messages": [
        {{"sender": "Tên Người 1", "voice": "female", "text": "Tin nhắn 1"}},
        {{"sender": "Tên Người 2", "voice": "male", "text": "Tin nhắn 2"}},
        ...
    ]
}}"""

    print("  Dang goi AI (qua OpenRouter)...", end=" ", flush=True)

    try:
        response = client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that strictly outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1500
        )
        
        raw_text = response.choices[0].message.content.strip()
        
        # Loại bỏ markdown ```json ... ``` nếu có
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1)
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "", 1)
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        # Parse JSON
        result = json.loads(raw_text)

        required_fields = ["title_vi", "hashtags", "messages"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Thieu truong '{field}' trong response")

        total_words = 0
        for msg in result["messages"]:
            total_words += len(msg["text"].split())

        result["word_count"] = total_words

        print(f"OK ({result['word_count']} tu)")
        return result

    except Exception as e:
        print(f"LOI: {e}")
        raise


def preview_script(translated: dict):
    """In preview kịch bản để người dùng kiểm tra."""
    print(f"\n{'='*70}")
    print("  KICH BAN TIENG VIET")
    print(f"{'='*70}")
    print(f"\nTieu de: {translated['title_vi']}")
    hashtags = translated.get('hashtags', '')
    if isinstance(hashtags, list):
        hashtags_str = ' '.join(['#' + h.replace('#', '') for h in hashtags])
    else:
        hashtags_str = hashtags
    print(f"\nHashtags: {hashtags_str}")
    print(f"\nKich ban Chat ({translated['word_count']} tu):\n")
    for msg in translated["messages"]:
        print(f"[{msg['sender']} - {msg['voice']}]: {msg['text']}")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    client = setup_gemini()

    test_post = {
        "subreddit": "confessions",
        "title": "I've been pretending to go to work for 6 months",
        "text": """Six months ago I was fired from my job. I was too ashamed to tell my wife and kids.
        So every morning, I put on my suit, kiss my family goodbye, drive to the coffee shop and spend 8 hours job hunting.
        I've managed to keep the money situation stable from savings and some freelance gigs.
        My wife thinks everything is fine. The guilt is eating me alive."""
    }

    result = translate_and_dramatize(test_post, client)
    preview_script(result)
    print("JSON output:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
