from moviepy.editor import VideoFileClip

print("Đang nén video nền...")
clip = VideoFileClip("assets/backgrounds/overcooked.mp4")
# Lấy đoạn 2 phút từ phút thứ 1
clip = clip.subclip(60, 180)
# Giảm độ phân giải (chiều cao xuống 1280, chiều rộng tự tỉ lệ)
clip = clip.resize(height=1280)
# Bỏ audio
clip = clip.without_audio()

clip.write_videofile(
    "assets/backgrounds/overcooked_light.mp4",
    fps=30,
    codec="libx264",
    bitrate="2000k",
    preset="fast",
    threads=4
)
print("Hoàn thành nén video!")
