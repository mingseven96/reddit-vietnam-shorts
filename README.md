# 🔥 Reddit Vietnam Shorts Generator

Công cụ tự động tạo video ngắn (YouTube Shorts / TikTok) từ các câu chuyện hot trên Reddit, được dịch sang tiếng Việt và viết lại theo phong cách giật gân, kích thích tò mò.

## ✨ Tính năng

- **Tự động cào Reddit**: Lấy bài đăng trending từ các subreddit hấp dẫn nhất (AITA, Confessions, v.v.)
- **Dịch thuật AI**: Dùng Gemini AI để dịch và viết lại kịch bản tiếng Việt gây sốc, viral
- **Giọng đọc tự nhiên**: Text-to-Speech bằng Microsoft Edge TTS (giọng Hoài My)
- **Phụ đề nhảy chữ**: Phụ đề highlight từng từ theo giọng đọc (dạng TikTok/Shorts)
- **Video hoàn chỉnh**: Xuất video dọc 9:16, 1080x1920px, chuẩn upload trực tiếp

## 🚀 Cài đặt

### Yêu cầu
- Python 3.9 trở lên
- ffmpeg (cần cài đặt riêng)

### Bước 1: Cài ffmpeg
```powershell
# Windows - dùng winget
winget install ffmpeg

# Hoặc tải tại: https://ffmpeg.org/download.html
```

### Bước 2: Cài thư viện Python
```powershell
pip install -r requirements.txt
```

### Bước 3: Lấy Gemini API Key (miễn phí)
1. Truy cập: https://aistudio.google.com/app/apikey
2. Đăng nhập Google và nhấn "Create API Key"
3. Mở `config.py` và điền key vào `GEMINI_API_KEY`

Hoặc set biến môi trường:
```powershell
$env:GEMINI_API_KEY = "your_key_here"
```

### Bước 4: Chuẩn bị video nền
Tải video gameplay (Minecraft, GTA, v.v.) hoặc ASMR không bản quyền và đặt vào thư mục:
```
assets/backgrounds/
```

Nguồn video miễn phí bản quyền:
- **Pexels**: https://www.pexels.com/search/videos/gaming/
- **Pixabay**: https://pixabay.com/videos/
- **yt-dlp** (Minecraft parkour CC videos trên YouTube)

## 🎬 Cách sử dụng

```powershell
python main.py
```

Công cụ sẽ tự động:
1. Tải các bài đăng hot từ Reddit
2. Hiển thị danh sách để bạn chọn
3. Dùng AI dịch và viết lại kịch bản tiếng Việt
4. Tạo giọng đọc AI
5. Ghép video hoàn chỉnh với phụ đề
6. Hiển thị title + hashtags để copy lên YouTube/TikTok

## ⚙️ Cấu hình

Mở `config.py` để tùy chỉnh:

| Biến | Mô tả | Mặc định |
|------|-------|---------|
| `SUBREDDITS` | Danh sách subreddit để cào | AmItheAsshole, confessions, v.v. |
| `TTS_VOICE` | Giọng đọc | `vi-VN-HoaiMyNeural` (giọng nữ) |
| `TARGET_VIDEO_DURATION_SECONDS` | Thời lượng video mục tiêu | 55 giây |
| `SUBTITLE_HIGHLIGHT_COLOR` | Màu highlight phụ đề | Vàng `#FFD700` |
| `BACKGROUND_OPACITY` | Độ tối video nền | 75% |
| `CHANNEL_WATERMARK` | Tên kênh watermark | `Reddit VN 🔥` |

## 📁 Cấu trúc thư mục

```
reddit-vietnam-shorts/
├── assets/
│   ├── backgrounds/    ← Đặt video nền vào đây
│   └── fonts/          ← Font chữ (tự tải)
├── output/             ← Video đầu ra
│   └── [timestamp]_[title]/
│       ├── video.mp4
│       ├── voice.mp3
│       ├── timing.json
│       └── metadata.json  ← Chứa title/hashtags/script để copy
├── config.py
├── reddit_scraper.py
├── translator.py
├── tts_generator.py
├── video_compiler.py
├── main.py
└── requirements.txt
```

## 💡 Tips kiếm nhiều view

- **Đăng giờ vàng**: 7-9h sáng, 12h trưa, 8-11h tối
- **TikTok**: 3-5 video/ngày để thuật toán đẩy mạnh
- **Subreddit hay nhất**: r/AmItheAsshole (mâu thuẫn gia đình), r/confessions (thú nhận giật gân)
- **Tiêu đề**: Luôn có emoji và kết thúc bằng "..." để gây tò mò
- **Tương tác**: Trả lời comment trong 1 giờ đầu để boost reach thuật toán
