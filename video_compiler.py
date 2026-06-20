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


def group_words_into_lines(word_boundaries: list[dict]) -> list[dict]:
    """
    Nhóm các từ thành các dòng phụ đề (tối đa SUBTITLE_MAX_WORDS_PER_LINE từ mỗi dòng).
    Mỗi dòng có thời gian bắt đầu, kết thúc và danh sách từ.
    """
    lines = []
    current_line_words = []

    for i, wb in enumerate(word_boundaries):
        current_line_words.append(wb)

        # Tạo dòng mới khi đủ số từ hoặc hết danh sách
        if len(current_line_words) >= SUBTITLE_MAX_WORDS_PER_LINE or i == len(word_boundaries) - 1:
            lines.append({
                "words": current_line_words.copy(),
                "start_ms": current_line_words[0]["offset_ms"],
                "end_ms": current_line_words[-1]["offset_ms"] + current_line_words[-1]["duration_ms"] + 200,
                "text": " ".join(w["word"] for w in current_line_words),
            })
            current_line_words = []

    return lines


def create_subtitle_frame(
    line: dict,
    current_time_ms: float,
    font_path: str,
    frame_size: tuple = (VIDEO_WIDTH, VIDEO_HEIGHT)
) -> np.ndarray:
    """
    Tạo một frame phụ đề với từ đang đọc được highlight màu vàng.
    Sử dụng Pillow để vẽ chữ có viền (stroke) rõ nét.
    """
    img = Image.new("RGBA", frame_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font = ImageFont.truetype(font_path, SUBTITLE_FONT_SIZE) if font_path else \
               ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    words = line["words"]
    text_parts = []

    for wb in words:
        is_active = wb["offset_ms"] <= current_time_ms < (wb["offset_ms"] + wb["duration_ms"] + 100)
        text_parts.append((wb["word"], is_active))

    # Tính vị trí tổng thể (canh giữa)
    full_text = " ".join(w for w, _ in text_parts)
    bbox = draw.textbbox((0, 0), full_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x_start = (frame_size[0] - text_width) // 2
    y_pos = int(frame_size[1] * SUBTITLE_Y_POSITION) - text_height // 2

    # Vẽ từng từ với màu sắc khác nhau
    x_cursor = x_start
    for i, (word, is_active) in enumerate(text_parts):
        word_display = word + (" " if i < len(text_parts) - 1 else "")
        word_bbox = draw.textbbox((0, 0), word_display, font=font)
        word_width = word_bbox[2] - word_bbox[0]

        color = SUBTITLE_HIGHLIGHT_COLOR if is_active else SUBTITLE_COLOR

        # Vẽ viền (stroke) bằng cách vẽ chữ nhiều lần xung quanh
        stroke = SUBTITLE_STROKE_WIDTH
        for dx in range(-stroke, stroke + 1):
            for dy in range(-stroke, stroke + 1):
                if dx != 0 or dy != 0:
                    draw.text((x_cursor + dx, y_pos + dy), word_display,
                              font=font, fill=SUBTITLE_STROKE_COLOR)

        # Vẽ chữ chính
        draw.text((x_cursor, y_pos), word_display, font=font, fill=color)
        x_cursor += word_width

    return np.array(img)


def compile_video(
    audio_path: str,
    word_boundaries: list[dict],
    translated: dict,
    output_dir: str,
    video_title: str,
    screenshot_path: str = None
) -> str:
    """
    Ghép video hoàn chỉnh: nền + audio + phụ đề chạy từng từ.

    Args:
        audio_path: Đường dẫn file audio .mp3
        word_boundaries: Danh sách thời gian từng từ
        translated: Dict kịch bản tiếng Việt (chứa title_vi, hashtags)
        output_dir: Thư mục lưu video đầu ra
        video_title: Tên file video (không có extension)

    Returns:
        Đường dẫn file video đầu ra
    """
    os.makedirs(output_dir, exist_ok=True)
    font_path = get_font_path()

    # 1. Load audio
    print("  🔊 Đang load audio...", end=" ", flush=True)
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    print(f"✅ ({duration:.1f}s)")

    # 2. Load và crop video nền
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
        # Video quá rộng -> cắt hai bên
        new_w = int(bg_h * target_ratio)
        x_center = bg_w // 2
        bg_clip = bg_clip.crop(x1=x_center - new_w // 2, x2=x_center + new_w // 2)
    else:
        # Video quá dọc -> cắt trên dưới
        new_h = int(bg_w / target_ratio)
        y_center = bg_h // 2
        bg_clip = bg_clip.crop(y1=y_center - new_h // 2, y2=y_center + new_h // 2)

    # Resize về đúng kích thước
    bg_clip = bg_clip.resize((VIDEO_WIDTH, VIDEO_HEIGHT))

    # Làm tối video nền để phụ đề nổi bật hơn
    bg_clip = bg_clip.fl_image(
        lambda frame: (frame * BACKGROUND_OPACITY).astype(np.uint8)
    )
    print("✅")

    # 3. Tạo phụ đề (dùng moviepy TextClip đơn giản)
    print("  📝 Đang tạo phụ đề...", end=" ", flush=True)
    subtitle_lines = group_words_into_lines(word_boundaries)
    subtitle_clips = []

    for line in subtitle_lines:
        start_sec = line["start_ms"] / 1000
        end_sec = min(line["end_ms"] / 1000, duration)
        line_duration = end_sec - start_sec

        if line_duration <= 0:
            continue

        # Mỗi từ trong dòng tạo ra một TextClip riêng (highlight từng từ)
        for wb in line["words"]:
            word_start = wb["offset_ms"] / 1000
            word_end = min((wb["offset_ms"] + wb["duration_ms"]) / 1000 + 0.1, duration)

            if word_end <= word_start:
                continue

            # Text clip cho toàn bộ dòng (màu trắng - background)
            try:
                bg_text = TextClip(
                    line["text"],
                    fontsize=SUBTITLE_FONT_SIZE,
                    color=SUBTITLE_COLOR,
                    stroke_color=SUBTITLE_STROKE_COLOR,
                    stroke_width=SUBTITLE_STROKE_WIDTH,
                    method="caption",
                    size=(VIDEO_WIDTH - 80, None),
                    align="center",
                )
                bg_text = bg_text.set_start(start_sec).set_duration(line_duration)
                bg_text = bg_text.set_position(("center", int(VIDEO_HEIGHT * SUBTITLE_Y_POSITION)))
                subtitle_clips.append(bg_text)
            except Exception:
                pass

            # Text clip cho từ đang được highlight (màu vàng)
            try:
                hl_text = TextClip(
                    wb["word"],
                    fontsize=SUBTITLE_FONT_SIZE + 4,
                    color=SUBTITLE_HIGHLIGHT_COLOR,
                    stroke_color=SUBTITLE_STROKE_COLOR,
                    stroke_width=SUBTITLE_STROKE_WIDTH,
                    method="label",
                )
                hl_text = hl_text.set_start(word_start).set_duration(word_end - word_start)
                # Vị trí highlight ở giữa dòng (đơn giản hóa)
                hl_text = hl_text.set_position(("center", int(VIDEO_HEIGHT * SUBTITLE_Y_POSITION)))
                subtitle_clips.append(hl_text)
            except Exception:
                pass

            break  # Chỉ xử lý một lần cho mỗi dòng (tối ưu)

    print(f"✅ ({len(subtitle_lines)} dòng)")

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
    layers = [bg_clip]
    
    # Overlay Reddit screenshot (hiển thị trong 4 giây đầu)
    if screenshot_path and os.path.exists(screenshot_path):
        try:
            ss_clip = ImageClip(screenshot_path)
            # Thu nhỏ lại cho vừa chiều ngang màn hình (chiếm 90% chiều ngang)
            ss_w = int(VIDEO_WIDTH * 0.9)
            ss_clip = ss_clip.resize(width=ss_w)
            
            # Tính toán vị trí Y sao cho nó nằm ở nửa trên màn hình
            y_pos = int(VIDEO_HEIGHT * 0.2)
            
            ss_clip = (ss_clip
                       .set_position(("center", y_pos))
                       .set_start(0)
                       .set_duration(duration))
            layers.append(ss_clip)
        except Exception as e:
            print(f"\n  [!] Lỗi thêm screenshot: {e}")

    # Thêm subtitle clips
    layers.extend(subtitle_clips)
    
    if watermark:
        layers.append(watermark)

    final = CompositeVideoClip(layers, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
    final = final.set_audio(audio_clip)
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
    audio_clip.close()
    bg_clip.close()
    final.close()

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✅\n  📁 File: {output_path} ({file_size_mb:.1f} MB)")

    return output_path


if __name__ == "__main__":
    print("Chạy video_compiler.py độc lập: cần có audio và timing data từ tts_generator.py trước.")
