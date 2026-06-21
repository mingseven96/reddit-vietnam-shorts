"""
tts_generator.py - Tạo giọng đọc AI từ kịch bản tiếng Việt
Sử dụng Microsoft Edge TTS (miễn phí, không cần API key)
Xuất file .mp3 và dữ liệu thời gian của từng từ cho phụ đề.
"""

import asyncio
import json
import os
import edge_tts
from config import TTS_RATE

VOICE_MALE = "vi-VN-NamMinhNeural"
VOICE_FEMALE = "vi-VN-HoaiMyNeural"

async def _generate_speech_async(text: str, voice: str, output_audio_path: str):
    """
    Hàm async tạo giọng đọc và lấy thời gian từng từ (Word Boundary).

    Args:
        text: Kịch bản tiếng Việt cần đọc
        output_audio_path: Đường dẫn lưu file audio .mp3
        output_timing_path: Đường dẫn lưu file timing .json
    """
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=TTS_RATE,
    )
    await communicate.save(output_audio_path)


def generate_chat_audio(messages: list, output_dir: str) -> list[dict]:
    """
    Tạo các file audio riêng biệt cho từng tin nhắn với giọng Nam/Nữ tương ứng.

    Args:
        messages: Mảng các tin nhắn
        output_dir: Thư mục lưu file

    Returns:
        Mảng thông tin audio: [{"index": 0, "audio_path": "...", "duration": 2.5}, ...]
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"  🎙️  Đang tạo giọng đọc cho {len(messages)} tin nhắn...", end=" ", flush=True)
    
    results = []
    
    for i, msg in enumerate(messages):
        audio_path = os.path.join(output_dir, f"msg_{i:03d}.mp3")
        voice = VOICE_FEMALE if msg.get("voice", "female") == "female" else VOICE_MALE
        
        asyncio.run(
            _generate_speech_async(msg["text"], voice, audio_path)
        )
        
        dur = get_audio_duration(audio_path)
        
        results.append({
            "index": i,
            "audio_path": audio_path,
            "duration": dur
        })

    print("✅")
    return results


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
