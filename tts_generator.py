"""
tts_generator.py - Tạo giọng đọc AI từ kịch bản tiếng Việt
Sử dụng Microsoft Edge TTS (miễn phí, không cần API key)
Xuất file .mp3 và dữ liệu thời gian của từng từ cho phụ đề.
"""

import asyncio
import json
import os
import edge_tts
from config import TTS_VOICE, TTS_RATE


async def _generate_speech_async(text: str, output_audio_path: str, output_timing_path: str):
    """
    Hàm async tạo giọng đọc và lấy thời gian từng từ (Word Boundary).

    Args:
        text: Kịch bản tiếng Việt cần đọc
        output_audio_path: Đường dẫn lưu file audio .mp3
        output_timing_path: Đường dẫn lưu file timing .json
    """
    communicate = edge_tts.Communicate(
        text=text,
        voice=TTS_VOICE,
        rate=TTS_RATE,
    )

    word_boundaries = []

    with open(output_audio_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_boundaries.append({
                    "word": chunk["text"],
                    "offset_ms": chunk["offset"] / 10000,
                    "duration_ms": chunk["duration"] / 10000,
                })
            elif chunk["type"] == "SentenceBoundary":
                # Fallback cho giọng tiếng Việt không hỗ trợ WordBoundary
                words = chunk["text"].split()
                if words:
                    dur_per_word = chunk["duration"] / len(words)
                    for i, w in enumerate(words):
                        word_boundaries.append({
                            "word": w,
                            "offset_ms": (chunk["offset"] + i * dur_per_word) / 10000,
                            "duration_ms": dur_per_word / 10000
                        })

    # Lưu timing data
    with open(output_timing_path, "w", encoding="utf-8") as f:
        json.dump(word_boundaries, f, ensure_ascii=False, indent=2)

    return word_boundaries


def generate_speech(text: str, output_dir: str) -> tuple[str, str, list[dict]]:
    """
    Tạo giọng đọc từ kịch bản văn bản.

    Args:
        text: Kịch bản tiếng Việt
        output_dir: Thư mục lưu file

    Returns:
        (audio_path, timing_path, word_boundaries)
    """
    os.makedirs(output_dir, exist_ok=True)

    audio_path = os.path.join(output_dir, "voice.mp3")
    timing_path = os.path.join(output_dir, "timing.json")

    print(f"  🎙️  Đang tạo giọng đọc ({TTS_VOICE})...", end=" ", flush=True)

    word_boundaries = asyncio.run(
        _generate_speech_async(text, audio_path, timing_path)
    )

    # Tính tổng thời lượng audio
    if word_boundaries:
        last = word_boundaries[-1]
        total_ms = last["offset_ms"] + last["duration_ms"]
        total_sec = total_ms / 1000
        print(f"✅ ({total_sec:.1f} giây, {len(word_boundaries)} từ)")
    else:
        print("✅")

    return audio_path, timing_path, word_boundaries


def get_audio_duration(audio_path: str) -> float:
    """
    Lấy thời lượng của file audio (giây).

    Args:
        audio_path: Đường dẫn file .mp3

    Returns:
        Thời lượng tính bằng giây
    """
    try:
        from mutagen.mp3 import MP3
        audio = MP3(audio_path)
        return audio.info.length
    except Exception:
        # Fallback: dùng moviepy
        from moviepy.editor import AudioFileClip
        with AudioFileClip(audio_path) as clip:
            return clip.duration


if __name__ == "__main__":
    # Test module độc lập
    test_text = """Tôi vừa hủy hoại cuộc hôn nhân của anh trai mình - và thật ra tôi không hề hối hận.
    Chuyện xảy ra vào đúng ngày cưới của anh, khi tôi phát hiện ra sự thật động trời về người phụ nữ anh sắp cưới."""

    audio, timing, boundaries = generate_speech(test_text, "temp_test")

    print(f"\nFile audio: {audio}")
    print(f"File timing: {timing}")
    print(f"\n5 từ đầu tiên:")
    for wb in boundaries[:5]:
        print(f"  '{wb['word']}' - bắt đầu: {wb['offset_ms']:.0f}ms, kéo dài: {wb['duration_ms']:.0f}ms")
