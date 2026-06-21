"""
video_compiler.py - Ghép video nền, audio và phụ đề chạy từng từ
Xuất video dọc (9:16) chuẩn YouTube Shorts / TikTok
"""

import os
import random
import math
import textwrap
import numpy as np
from moviepy.editor import (
    AudioFileClip,
    VideoFileClip,
    TextClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
    concatenate_audioclips,
)
from PIL import Image, ImageDraw, ImageFont
import glob

from config import (
    BACKGROUNDS_DIR, FONTS_DIR, FONT_FILE,
    VIDEO_WIDTH, VIDEO_HEIGHT,
    SUBTITLE_FONT_SIZE, SUBTITLE_COLOR, SUBTITLE_HIGHLIGHT_COLOR,
    SUBTITLE_STROKE_COLOR, SUBTITLE_STROKE_WIDTH,
    SUBTITLE_Y_POSITION, SUBTITLE_MAX_WORDS_PER_LINE,
    BACKGROUND_OPACITY, OUTPUT_DIR, CHANNEL_WATERMARK
)


def get_random_background() -> str:
    """Lấy một video nền ngẫu nhiên từ thư mục backgrounds."""
    patterns = [
        os.path.join(BACKGROUNDS_DIR, "*.mp4"),
        os.path.join(BACKGROUNDS_DIR, "*.mov"),
        os.path.join(BACKGROUNDS_DIR, "*.avi"),
    ]

    all_videos = []
    for pattern in patterns:
        all_videos.extend(glob.glob(pattern))

    if not all_videos:
        raise FileNotFoundError(
            f"❌ Không tìm thấy video nền trong '{BACKGROUNDS_DIR}'.\n"
            f"   Hãy tải video gameplay (Minecraft, GTA, v.v.) hoặc video ASMR "
            f"vào thư mục '{BACKGROUNDS_DIR}' và thử lại."
        )

    selected = random.choice(all_videos)
    print(f"  🎬 Video nền: {os.path.basename(selected)}")
    return selected


def get_font_path() -> str:
    """Lấy đường dẫn file font, tải về nếu chưa có."""
    font_path = os.path.join(FONTS_DIR, FONT_FILE)

    if not os.path.exists(font_path):
        os.makedirs(FONTS_DIR, exist_ok=True)
        print(f"  ⚠️  Font '{FONT_FILE}' chưa có. Đang tải về...")
        try:
            import urllib.request
            font_url = (
                "https://github.com/google/fonts/raw/main/ofl/montserrat/"
                "Montserrat%5Bwght%5D.ttf"
            )
            urllib.request.urlretrieve(font_url, font_path)
            print(f"  ✅ Đã tải font: {font_path}")
        except Exception as e:
            print(f"  ⚠️  Không tải được font: {e}. Dùng font mặc định.")
            return None

    return font_path


# (Removed create_subtitle_frame and group_words_into_lines since we use Chat Bubbles now)


def compile_video(
    audio_items: list[dict],
    chat_states: list[str],
    translated: dict,
    output_dir: str,
    video_title: str
) -> str:
    """
    Ghép video hoàn chỉnh: nền + chuỗi audio + chuỗi ảnh chat bubble.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Ghép Audio
    print("  🔊 Đang ghép chuỗi audio...", end=" ", flush=True)
    audio_clips = [AudioFileClip(item["audio_path"]) for item in audio_items]
    final_audio = concatenate_audioclips(audio_clips)
    duration = final_audio.duration
    print(f"✅ ({duration:.1f}s)")

    # 2. Ghép hình ảnh Chat
    print("  💬 Đang tạo chuỗi ảnh chat...", end=" ", flush=True)
    image_clips = []
    for i in range(len(audio_items)):
        dur = audio_clips[i].duration
        img_path = chat_states[i]
        
        # Thêm 0.2s pause sau mỗi tin nhắn cho tự nhiên
        img_clip = ImageClip(img_path).set_duration(dur)
        image_clips.append(img_clip)
        
    chat_video = concatenate_videoclips(image_clips, method="compose")
    print("✅")

    # 3. Load và crop video nền
    print("  🎬 Đang xử lý video nền...", end=" ", flush=True)
    bg_path = get_random_background()
    bg_clip = VideoFileClip(bg_path)

    # Nếu video nền ngắn hơn audio, loop lại
    if bg_clip.duration < duration:
        loops_needed = math.ceil(duration / bg_clip.duration)
        bg_clip = concatenate_videoclips([bg_clip] * loops_needed)

    # Chọn điểm bắt đầu ngẫu nhiên
    max_start = bg_clip.duration - duration
    start_time = random.uniform(0, max(0, max_start))
    bg_clip = bg_clip.subclip(start_time, start_time + duration)

    # Crop về tỉ lệ 9:16 (dọc)
    bg_w, bg_h = bg_clip.size
    target_ratio = VIDEO_WIDTH / VIDEO_HEIGHT

    if bg_w / bg_h > target_ratio:
        new_w = int(bg_h * target_ratio)
        x_center = bg_w // 2
        bg_clip = bg_clip.crop(x1=x_center - new_w // 2, x2=x_center + new_w // 2)
    else:
        new_h = int(bg_w / target_ratio)
        y_center = bg_h // 2
        bg_clip = bg_clip.crop(y1=y_center - new_h // 2, y2=y_center + new_h // 2)

    bg_clip = bg_clip.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
    
    # Làm mờ video nền một chút để chat nổi hơn
    bg_clip = bg_clip.fl_image(
        lambda frame: (frame * BACKGROUND_OPACITY).astype(np.uint8)
    )
    print("✅")

    # 4. Watermark kênh
    try:
        watermark = TextClip(
            CHANNEL_WATERMARK,
            fontsize=36,
            color="#FFFFFF",
            stroke_color="#000000",
            stroke_width=2,
        )
        watermark = watermark.set_duration(duration)
        watermark = watermark.set_position((VIDEO_WIDTH - 280, 60))
        watermark = watermark.set_opacity(0.85)
    except Exception:
        watermark = None

    # 5. Ghép tất cả layers
    print("  🎞️  Đang render video (có thể mất vài phút)...", end=" ", flush=True)
    
    # Đặt chat video ở giữa màn hình
    chat_video = chat_video.set_position("center")
    
    layers = [bg_clip, chat_video]
    if watermark:
        layers.append(watermark)

    final = CompositeVideoClip(layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    final = final.set_audio(final_audio)
    final = final.set_duration(duration)

    # 6. Xuất file
    output_filename = f"{video_title}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="4000k",
        audio_bitrate="192k",
        threads=4,
        preset="fast",
        verbose=False,
        logger=None,
    )

    # Dọn dẹp
    for a in audio_clips:
        a.close()
    final_audio.close()
    bg_clip.close()
    final.close()

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅\n  📁 File: {output_path} ({file_size_mb:.1f} MB)")

    return output_path


if __name__ == "__main__":
    print("Chạy video_compiler.py độc lập: cần có audio và timing data từ tts_generator.py trước.")
