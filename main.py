"""
main.py - Điều phối quy trình tạo video Fake Chat (Zalo/iMessage) tiếng Việt từ Reddit
Luồng: Cào Reddit -> AI tạo Chat -> Render giao diện Chat -> TTS 2 giọng -> Video Overlay
"""

import os
import sys
import io
import json
import time
import re
import shutil
from datetime import datetime

# Fix Unicode encoding cho Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from config import GEMINI_API_KEY, OUTPUT_DIR
from reddit_scraper import fetch_with_requests
from translator import setup_gemini, translate_and_dramatize, preview_script
from tts_generator import generate_chat_audio
from video_compiler import compile_video
from chat_generator import generate_chat_states


BANNER = """
+--------------------------------------------------------------+
|                                                              |
|   Fake Chat Shorts Generator                                 |
|   Tu dong: Reddit -> AI Chat -> TTS -> Render Video          |
|                                                              |
+--------------------------------------------------------------+
"""


def check_api_key():
    """Kiểm tra API key Gemini đã được cấu hình chưa."""
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE" or not GEMINI_API_KEY:
        print("❌ Bạn chưa cấu hình Gemini API Key!")
        print("\n📋 Hướng dẫn lấy API Key miễn phí:")
        print("   1. Truy cập: https://aistudio.google.com/app/apikey")
        print("   2. Đăng nhập bằng Google Account")
        print("   3. Nhấn 'Create API Key'")
        print("   4. Mở file config.py và điền key vào dòng GEMINI_API_KEY")
        print("\n   Hoặc set biến môi trường:")
        print("   $env:GEMINI_API_KEY = 'your_key_here'   (PowerShell)")
        print()
        sys.exit(1)


def check_backgrounds_dir():
    """Kiểm tra thư mục backgrounds và hướng dẫn nếu trống."""
    import glob
    bg_files = glob.glob(os.path.join("assets/backgrounds", "*.mp4"))
    bg_files += glob.glob(os.path.join("assets/backgrounds", "*.mov"))

    if not bg_files:
        print("⚠️  Thư mục assets/backgrounds/ chưa có video nền!")
        print("\n📋 Hướng dẫn tải video nền miễn phí (không bản quyền):")
        print("   1. Tải video Minecraft parkour từ YouTube (dùng yt-dlp)")
        print("      yt-dlp -o assets/backgrounds/minecraft.mp4 <youtube_url>")
        print("   2. Hoặc tải từ Pexels.com (tìm 'gameplay background')")
        print("   3. Đặt file .mp4 vào thư mục: assets/backgrounds/")
        print()

        choice = input("Bạn muốn tiếp tục không (bỏ qua bước tạo video)? [y/N]: ").strip().lower()
        return choice == "y"

    return True


def sanitize_filename(title: str) -> str:
    """Làm sạch tiêu đề để dùng làm tên file."""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", title)
    sanitized = sanitized.replace(" ", "_")
    return sanitized[:80]  # Giới hạn độ dài


def save_metadata(post: dict, translated: dict, video_path: str, output_dir: str):
    """Lưu metadata của video (title, hashtags, nguồn) vào file JSON."""
    metadata = {
        "created_at": datetime.now().isoformat(),
        "source_post": {
            "platform": "Reddit",
            "title": post.get("title"),
            "url": post.get("url"),
            "score": post.get("score"),
        },
        "video": {
            "title_vi": translated["title_vi"],
            "hashtags": translated["hashtags"],
            "messages": translated["messages"],
            "word_count": translated["word_count"],
            "output_file": video_path,
        },
        "youtube_upload_info": {
            "recommended_title": translated["title_vi"],
            "recommended_description": (
                f"Bóc phốt cực căng 😱\n\n"
                f"{'  '.join(['#' + h for h in translated['hashtags']])}\n\n"
                f"#Drama #LuatNhanGua #NgoaiTinh #Shorts"
            ),
            "recommended_tags": translated.get("hashtags", []) if isinstance(translated.get("hashtags"), list) else [translated.get("hashtags", "")] + ["Drama", "Zalo", "FakeChat", "Shorts"],
        }
    }

    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n  💾 Metadata đã lưu: {metadata_path}")


def print_upload_guide(translated: dict, video_path: str):
    """In hướng dẫn upload YouTube/TikTok sau khi hoàn thành."""
    hashtag_str = " ".join(["#" + h for h in translated["hashtags"]])

    print(f"\n{'='*70}")
    print("  🚀 HƯỚNG DẪN UPLOAD")
    print(f"{'='*70}")
    print(f"\n📹 File video: {video_path}")
    print(f"\n🏷️  Tiêu đề YouTube/TikTok:")
    print(f"   {translated['title_vi']}")
    hashtags = translated.get('hashtags', '')
    if isinstance(hashtags, list):
        hashtag_str = " ".join(["#" + h.replace('#', '') for h in hashtags])
    else:
        hashtag_str = hashtags
    
    print(f"\n#️⃣  Hashtags:")
    print(f"   {hashtag_str} #ThreadsVN #Shorts")
    print(f"\n📋 Copy mô tả này vào YouTube:")
    print(f"   Bóc phốt cực căng 😱 Hãy xem đến cuối...")
    print(f"\n{'='*70}")
    print("  ✅ Tips để video viral:")
    print("  • Đăng vào khung giờ vàng: 7h-9h sáng, 12h trưa, 8h-11h tối")
    print("  • TikTok: 3-5 video/ngày để đẩy thuật toán")
    print("  • YouTube Shorts: Dùng tiêu đề có emoji và dấu hỏi/chấm than")
    print("  • Trả lời tất cả comment trong 1h đầu để boost reach")
    print(f"{'='*70}\n")


def run():
    """Hàm chính điều phối toàn bộ quy trình."""
    print(BANNER)

    # ─── Kiểm tra cấu hình ───────────────────────────────────────
    check_api_key()

    # ─── Tạo thư mục cần thiết ───────────────────────────────────
    os.makedirs("assets/backgrounds", exist_ok=True)
    os.makedirs("assets/fonts", exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ─── Bước 1: Lấy bài đăng Reddit ─────────────────────────────
    print("📡 BƯỚC 1/4: Tải bài đăng từ Reddit\n")
    sub = input("🔗 Nhập subreddit (VD: confessions, TrueOffMyChest): ").strip()
    if not sub:
        sub = "confessions"
        
    print(f"  Đang cào bài hot từ r/{sub}...")
    posts = fetch_with_requests(sub, limit=3)

    if not posts:
        print("❌ Không tải được nội dung từ Reddit. Sử dụng kịch bản mẫu để demo.")
        posts = [{
            "title": "Mẹ chồng vứt bỏ bộ sưu tập truyện tranh 100 triệu của tôi",
            "url": "https://reddit.com/r/demo",
            "score": 55000,
            "text": "Tôi có một bộ sưu tập truyện tranh hiếm trị giá khoảng 100 triệu, được cất cẩn thận trong tủ kính. Hôm qua đi làm về, tôi thấy mẹ chồng đang đem cho thằng cháu họ xa mấy cuốn truyện của tôi. Bà bảo 'mấy quyển truyện tranh trẻ con này có gì mà quý'. Tôi đã cãi nhau to với bà và yêu cầu bà phải đền tiền. Bây giờ cả nhà chồng đang chửi tôi hỗn láo. Tôi có sai không?"
        }]

    selected_post = posts[0] # Lấy bài top 1
    print(f"\n✅ Đã lấy dữ liệu: {selected_post['title']}")

    # ─── Bước 3: Dịch và viết lại kịch bản ──────────────────────
    print(f"\n🤖 BƯỚC 3/4: Dịch và viết lại kịch bản tiếng Việt\n")
    model = setup_gemini()
    translated = translate_and_dramatize(selected_post, model)
    preview_script(translated)

    # Hỏi người dùng có muốn chỉnh sửa kịch bản không
    confirm = input("Bạn có muốn tiếp tục tạo video với kịch bản này không? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("❌ Đã hủy. Chạy lại để thử kịch bản khác.")
        sys.exit(0)

    # ─── Tạo thư mục output cho video này ────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = sanitize_filename(translated["title_vi"])
    video_session_dir = os.path.join(OUTPUT_DIR, f"{timestamp}_{safe_title[:40]}")
    os.makedirs(video_session_dir, exist_ok=True)

    # ─── Bước 4a: Tạo ảnh & giọng đọc ────────────────────────────
    print(f"\n🎙️  BƯỚC 4/4: Tạo UI Chat & Giọng đọc + Render video\n")
    
    # Tạo ảnh Chat
    chat_states = generate_chat_states(translated["messages"], video_session_dir)
    
    # Tạo audio cho từng tin nhắn
    audio_items = generate_chat_audio(translated["messages"], video_session_dir)

    if not audio_items or not chat_states:
        print("❌ Không tạo được Audio/Image. Thử lại.")
        sys.exit(1)

    # ─── Bước 4b: Ghép video ──────────────────────────────────────
    has_backgrounds = check_backgrounds_dir()

    if has_backgrounds:
        video_path = compile_video(
            audio_items=audio_items,
            chat_states=chat_states,
            translated=translated,
            output_dir=video_session_dir,
            video_title=safe_title[:60],
        )

        # Lưu metadata
        save_metadata(selected_post, translated, video_path, video_session_dir)

        # In hướng dẫn upload
        print_upload_guide(translated, video_path)

    else:
        # Không có video nền -> chỉ lưu audio và kịch bản
        print(f"\n  📁 Đã tạo audio và ảnh chat tại: {video_session_dir}/")

        # Lưu kịch bản ra file text
        script_path = os.path.join(video_session_dir, "script.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(f"TIÊU ĐỀ: {translated['title_vi']}\n\n")
            f.write(f"KỊCH BẢN CHAT:\n")
            for msg in translated["messages"]:
                f.write(f"[{msg['sender']} - {msg['voice']}]: {msg['text']}\n")
        print(f"     📄 Kịch bản: {script_path}")

    print("\n✅ Hoàn thành! Chúc bạn kiếm được nhiều view! 🚀\n")


if __name__ == "__main__":
    run()
