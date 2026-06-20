"""
config.py - Cấu hình trung tâm cho Reddit Vietnam Shorts
Chỉnh sửa các giá trị dưới đây trước khi chạy công cụ.
"""

import os

# ─────────────────────────────────────────────
# 🔑 API Keys
# Lấy Gemini API Key miễn phí tại: https://aistudio.google.com/app/apikey
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ─────────────────────────────────────────────
# 🤖 Reddit API Credentials (TUY CHON - de cao nhanh hon)
# Tao app mien phi tai: https://www.reddit.com/prefs/apps
# Chon loai: 'script', Redirect URI: http://localhost:8080
# ─────────────────────────────────────────────
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "RedditVNShorts/1.0")

# ─────────────────────────────────────────────
# 📡 Reddit Scraper Settings
# ─────────────────────────────────────────────
SUBREDDITS = [
    "AmItheAsshole",       # Chuyện tranh cãi, xung đột
    "confessions",         # Lời thú nhận gây sốc
    "relationship_advice", # Chuyện tình cảm, hôn nhân
    "tifu",                # "Today I Fucked Up" - Những sự cố hài hước/đáng xấu hổ
    "entitledparents",     # Chuyện phụ huynh bất lịch sự
    "pettyrevenge",        # Báo thù nhỏ nhưng đỉnh
]

# Lấy top bao nhiêu bài từ mỗi subreddit
POSTS_PER_SUBREDDIT = 5

# Số từ tối thiểu của bài đăng (lọc bài quá ngắn)
MIN_POST_WORDS = 100

# ─────────────────────────────────────────────
# 🤖 AI / Dịch thuật Settings
# ─────────────────────────────────────────────
GEMINI_MODEL = "google/gemini-2.5-flash"

# Thời lượng mục tiêu của video (giây)
TARGET_VIDEO_DURATION_SECONDS = 55  # Chuẩn cho Shorts/TikTok (dưới 60 giây)

# Tốc độ đọc trung bình (từ/phút) để ước tính số từ cho phù hợp thời lượng
WORDS_PER_MINUTE = 130

# ─────────────────────────────────────────────
# 🎙️ Text-to-Speech Settings
# ─────────────────────────────────────────────
# Giọng đọc tiếng Việt từ Microsoft Edge TTS
# Giọng nữ: vi-VN-HoaiMyNeural
# Giọng nam: vi-VN-NamMinhNeural
TTS_VOICE = "vi-VN-HoaiMyNeural"

# Tốc độ đọc: "+0%" là bình thường, "+10%" nhanh hơn 10%
TTS_RATE = "+15%"

# ─────────────────────────────────────────────
# 🎬 Video Settings
# ─────────────────────────────────────────────
# Thư mục chứa video nền (đặt các file .mp4 vào đây)
BACKGROUNDS_DIR = "assets/backgrounds"

# Thư mục chứa font chữ
FONTS_DIR = "assets/fonts"

# Tên file font (sẽ tải tự động nếu không tồn tại)
FONT_FILE = "Montserrat-Bold.ttf"

# Độ phân giải video đầu ra (9:16 dọc, chuẩn Shorts)
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

# Cài đặt phụ đề
SUBTITLE_FONT_SIZE = 70
SUBTITLE_COLOR = "#FFFFFF"          # Màu chữ mặc định
SUBTITLE_HIGHLIGHT_COLOR = "#FFD700"  # Màu chữ khi đang được đọc (vàng gold)
SUBTITLE_STROKE_COLOR = "#000000"   # Viền chữ đen để dễ đọc
SUBTITLE_STROKE_WIDTH = 3
SUBTITLE_Y_POSITION = 0.65          # Vị trí phụ đề (65% từ trên xuống)
SUBTITLE_MAX_WORDS_PER_LINE = 5     # Số từ tối đa trên 1 dòng

# Hiệu ứng mờ (opacity) của video nền
BACKGROUND_OPACITY = 0.75           # 75% độ sáng (làm tối bớt để chữ nổi bật)

# ─────────────────────────────────────────────
# 📁 Thư mục đầu ra
# ─────────────────────────────────────────────
OUTPUT_DIR = "output"

# ─────────────────────────────────────────────
# 🖥️ Header video (Card mở đầu video)
# ─────────────────────────────────────────────
CHANNEL_WATERMARK = "Reddit VN 🔥"  # Tên kênh hiển thị góc trên phải
