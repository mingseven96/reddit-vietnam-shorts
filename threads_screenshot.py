import os
from html2image import Html2Image

def generate_threads_screenshot(post: dict, output_dir: str) -> str:
    """
    Tạo ảnh screenshot Threads post giả lập bằng HTML/CSS
    """
    hti = Html2Image(size=(900, 450))
    
    author = post.get("author", "anonymous")
    text = post.get("text", "Drama Threads...")
    
    # Rút gọn text nếu quá dài
    if len(text) > 250:
        text = text[:250] + "..."
        
    score = post.get("score", "12.5K")
    comments = post.get("num_comments", "1.2K")

    html_template = f"""
    <html lang="en">
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            body {{
                background-color: transparent;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .threads-card {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #101010;
                border-radius: 24px;
                border: 1px solid #333333;
                padding: 24px;
                color: #F3F5F7;
                width: 750px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.6);
            }}
            .header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 16px;
            }}
            .header-left {{
                display: flex;
                align-items: center;
            }}
            .avatar {{
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(45deg, #f09433 0%, #e6683c 25%, #dc2743 50%, #cc2366 75%, #bc1888 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                margin-right: 12px;
                font-weight: bold;
                font-size: 18px;
            }}
            .author-info {{
                display: flex;
                flex-direction: column;
            }}
            .username {{
                font-size: 16px;
                font-weight: 600;
                color: #F3F5F7;
                line-height: 1.2;
            }}
            .time {{
                font-size: 14px;
                color: #777777;
                line-height: 1.2;
                margin-top: 2px;
            }}
            .threads-logo {{
                font-size: 24px;
            }}
            .content {{
                font-size: 20px;
                font-weight: 400;
                line-height: 1.5;
                margin-bottom: 20px;
                color: #F3F5F7;
                white-space: pre-wrap;
            }}
            .footer {{
                display: flex;
                align-items: center;
                gap: 24px;
                color: #777777;
            }}
            .action-btn {{
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 15px;
                font-weight: 500;
            }}
            .icon {{
                font-size: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="threads-card">
            <div class="header">
                <div class="header-left">
                    <div class="avatar">{author[0].upper() if author else "T"}</div>
                    <div class="author-info">
                        <span class="username">{author}</span>
                        <span class="time">2h</span>
                    </div>
                </div>
                <div class="threads-logo">@</div>
            </div>
            <div class="content">{text}</div>
            <div class="footer">
                <div class="action-btn">
                    <span class="icon">♡</span> {score}
                </div>
                <div class="action-btn">
                    <span class="icon">💬</span> {comments}
                </div>
                <div class="action-btn">
                    <span class="icon">🔁</span>
                </div>
                <div class="action-btn">
                    <span class="icon">➤</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    os.makedirs(output_dir, exist_ok=True)
    out_name = f"threads_post_{post.get('id', 'demo')}.png"
    out_path = os.path.join(output_dir, out_name)
    
    hti.screenshot(html_str=html_template, save_as=out_name)
    
    if os.path.exists(out_name):
        import shutil
        shutil.move(out_name, out_path)
        
    return out_path
