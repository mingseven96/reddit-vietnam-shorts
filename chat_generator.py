import os
from html2image import Html2Image

def generate_chat_states(messages: list, output_dir: str) -> list[str]:
    """
    Tạo danh sách các ảnh chụp màn hình (PNG trong suốt) cho từng trạng thái của đoạn chat.
    Mỗi trạng thái sẽ thêm 1 tin nhắn mới vào.
    
    Args:
        messages: Mảng các tin nhắn [{"sender": "A", "text": "...", "voice": "female"}, ...]
        output_dir: Thư mục lưu ảnh
        
    Returns:
        List các đường dẫn tới các ảnh trạng thái chat.
    """
    hti = Html2Image(size=(1080, 1920), custom_flags=['--default-background-color=00000000'])
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Xác định ai là người gửi (bên phải), ai là người nhận (bên trái)
    if not messages:
        return []
        
    sender_right = messages[0]["sender"]
    
    css = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    body {
        margin: 0;
        padding: 0;
        width: 1080px;
        height: 1920px;
        background-color: transparent;
        font-family: 'Inter', sans-serif;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        padding: 60px 40px;
        gap: 30px;
        max-height: 1600px;
        overflow: hidden;
    }
    .message-wrapper {
        display: flex;
        flex-direction: column;
        max-width: 80%;
    }
    .message-wrapper.right {
        align-self: flex-end;
        align-items: flex-end;
    }
    .message-wrapper.left {
        align-self: flex-start;
        align-items: flex-start;
    }
    .sender-name {
        font-size: 24px;
        color: #ffffff;
        margin-bottom: 8px;
        font-weight: 500;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    .bubble {
        padding: 24px 32px;
        border-radius: 36px;
        font-size: 42px;
        line-height: 1.4;
        color: #ffffff;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        word-wrap: break-word;
    }
    .right .bubble {
        background-color: #007AFF;
        border-bottom-right-radius: 8px;
    }
    .left .bubble {
        background-color: #3A3A3C;
        border-bottom-left-radius: 8px;
    }
    """
    
    state_images = []
    
    for i in range(len(messages)):
        current_msgs = messages[:i+1]
        
        html_content = f"<html><head><style>{css}</style></head><body><div class='chat-container'>"
        
        for msg in current_msgs:
            is_right = (msg["sender"] == sender_right)
            align_class = "right" if is_right else "left"
            
            html_content += f"""
            <div class='message-wrapper {align_class}'>
                <div class='sender-name'>{msg['sender']}</div>
                <div class='bubble'>{msg['text']}</div>
            </div>
            """
            
        html_content += "</div></body></html>"
        
        img_name = f"chat_state_{i:03d}.png"
        img_path = os.path.join(output_dir, img_name)
        
        hti.screenshot(html_str=html_content, save_as=img_name)
        
        # move to correct dir
        if os.path.exists(img_name):
            import shutil
            shutil.move(img_name, img_path)
            state_images.append(img_path)
            
    return state_images
