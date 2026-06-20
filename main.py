"""
main.py - Điều phối toàn bộ quy trình tạo video Reddit Shorts tiếng Việt
Luồng: Cào Reddit -> Chọn bài -> Dịch AI -> Tạo giọng đọc -> Render video
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
from reddit_scraper import fetch_all_trending_posts, display_posts_menu
from translator import setup_gemini, translate_and_dramatize, preview_script
from tts_generator import generate_speech
from video_compiler import compile_video
from reddit_screenshot import generate_reddit_screenshot


BANNER = """
+--------------------------------------------------------------+
|                                                              |
|   Reddit Vietnam Shorts Generator                            |
|   Tu dong: Cao Reddit -> Dich AI -> Giong doc -> Video       |
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
            "subreddit": post["subreddit"],
            "title_en": post["title"],
            "url": post["url"],
            "score": post["score"],
        },
        "video": {
            "title_vi": translated["title_vi"],
            "hashtags": translated["hashtags"],
            "script": translated["script"],
            "word_count": translated["word_count"],
            "output_file": video_path,
        },
        "youtube_upload_info": {
            "recommended_title": translated["title_vi"],
            "recommended_description": (
                f"{translated['script'][:300]}...\n\n"
                f"{'  '.join(['#' + h for h in translated['hashtags']])}\n\n"
                f"#RedditVN #RedditViệtNam #Shorts"
            ),
            "recommended_tags": translated["hashtags"] + ["Reddit", "RedditVN", "Shorts", "GiậtGân"],
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
    print(f"\n#️⃣  Hashtags:")
    print(f"   {hashtag_str} #RedditVN #Shorts")
    print(f"\n📋 Copy mô tả này vào YouTube:")
    print(f"   {translated['script'][:200]}...")
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

    # ─── Bước 1: Cào bài đăng Reddit ─────────────────────────────
    print("📡 BƯỚC 1/4: Tải bài đăng từ Reddit\n")
    posts = fetch_all_trending_posts(verbose=True)

    if not posts:
        print("❌ Không tải được bài đăng. Kiểm tra kết nối mạng và thử lại.")
        sys.exit(1)

    # ─── Bước 2: Người dùng chọn bài ─────────────────────────────
    print(f"\n🎯 BƯỚC 2/4: Chọn bài đăng\n")
    selected_post = display_posts_menu(posts)

    if not selected_post:
        sys.exit(0)

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

    # ─── Bước 4a: Tạo giọng đọc ──────────────────────────────────
    print(f"\n🎙️  BƯỚC 4/4: Tạo giọng đọc + Render video\n")
    audio_path, timing_path, word_boundaries = generate_speech(
        translated["script"],
        output_dir=video_session_dir,
    )

    if not word_boundaries:
        print("❌ Không tạo được dữ liệu timing. Kiểm tra edge-tts và thử lại.")
        sys.exit(1)

    # ─── Bước 4b: Ghép video ──────────────────────────────────────
    has_backgrounds = check_backgrounds_dir()

    if has_backgrounds:
        # Sinh ảnh screenshot Reddit
        screenshot_path = generate_reddit_screenshot(selected_post, video_session_dir)

        video_path = compile_video(
            audio_path=audio_path,
            word_boundaries=word_boundaries,
            translated=translated,
            output_dir=video_session_dir,
            video_title=safe_title[:60],
            screenshot_path=screenshot_path,
        )

        # Lưu metadata
        save_metadata(selected_post, translated, video_path, video_session_dir)

        # In hướng dẫn upload
        print_upload_guide(translated, video_path)

    else:
        # Không có video nền -> chỉ lưu audio và kịch bản
        print(f"\n  📁 Đã tạo:")
        print(f"     🎵 Audio: {audio_path}")
        print(f"     📝 Kịch bản + hashtags lưu tại: {video_session_dir}/")

        # Lưu kịch bản ra file text
        script_path = os.path.join(video_session_dir, "script.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(f"TIÊU ĐỀ: {translated['title_vi']}\n\n")
            f.write(f"HASHTAGS: {' '.join(['#' + h for h in translated['hashtags']])}\n\n")
            f.write(f"KỊCH BẢN:\n{translated['script']}")
        print(f"     📄 Kịch bản: {script_path}")

    print("\n✅ Hoàn thành! Chúc bạn kiếm được nhiều view! 🚀\n")


if __name__ == "__main__":
    run()
