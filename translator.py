"""
translator.py - Dịch và viết lại câu chuyện Reddit sang tiếng Việt giật gân
Sử dụng OpenAI SDK (kết nối OpenRouter) để tạo kịch bản viral miễn phí.
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
    Dịch và viết lại câu chuyện Reddit sang tiếng Việt dạng giật gân.

    Args:
        post: Dict chứa thông tin bài đăng Reddit
        client: OpenAI client kết nối qua OpenRouter

    Returns:
        Dict chứa: title_vi, hashtags, script
    """
    target_words = calculate_target_word_count()

    prompt = f"""Bạn là chuyên gia viết content viral cho TikTok và YouTube Shorts tại Việt Nam.
Nhiệm vụ của bạn là đọc một câu chuyện từ Reddit (tiếng Anh) và viết lại thành kịch bản đọc cho video ngắn tiếng Việt, với phong cách gây sốc, kích thích tò mò, cảm xúc mạnh.

--- THÔNG TIN BÀI ĐĂNG ---
Subreddit: r/{post['subreddit']}
Tiêu đề gốc: {post['title']}

Nội dung:
{post['text'][:3000]}
--- KẾT THÚC BÀI ĐĂNG ---

--- YÊU CẦU OUTPUT ---
Hãy trả về một JSON HỢP LỆ chính xác theo định dạng sau (không giải thích thêm):

{{
  "title_vi": "Tiêu đề tiếng Việt giật gân, gây tò mò tối đa (dưới 100 ký tự, dùng cho YouTube/TikTok)",
  "hashtags": ["hashtag1", "hashtag2", "hashtag3", "hashtag4", "hashtag5"],
  "script": "Toàn bộ kịch bản đọc tiếng Việt. Bắt đầu bằng một câu hook cực kỳ giật gân. Kể câu chuyện sinh động, dùng ngôn ngữ giới trẻ VN. Kết thúc bằng câu kêu gọi bình luận. Khoảng {target_words} từ."
}}

--- HƯỚNG DẪN VIẾT KỊCH BẢN ---
1. Câu Hook (3-5 giây đầu): Phải cực kỳ giật gân, đặt câu hỏi hoặc nêu tình huống sốc.
2. Phần thân: Kể câu chuyện nhanh, kịch tính, không lan man. Dùng "tôi", "anh ấy/cô ấy".
3. Câu kết: Kêu gọi tương tác: "Bạn nghĩ tôi đúng hay sai? Comment bên dưới nhé!"
4. Ngôn ngữ: Tự nhiên, gần gũi với giới trẻ VN (18-30 tuổi).
5. Không bịa: Chỉ được dịch và phóng tác, không thêm tình tiết không có trong bài gốc."""

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

        # Parse JSON
        result = json.loads(raw_text)

        required_fields = ["title_vi", "hashtags", "script"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Thieu truong '{field}' trong response")

        result["script"] = result["script"].strip()
        result["word_count"] = len(result["script"].split())

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
    print(f"\nHashtags: {' '.join(['#' + h for h in translated['hashtags']])}")
    print(f"\nKich ban ({translated['word_count']} tu):\n")
    print(translated["script"])
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
