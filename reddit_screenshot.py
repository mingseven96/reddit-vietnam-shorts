import os
from html2image import Html2Image

def generate_reddit_screenshot(post: dict, output_dir: str) -> str:
    """
    Tạo ảnh screenshot Reddit post giả lập bằng HTML/CSS
    """
    hti = Html2Image(size=(900, 400))
    
    subreddit = post.get("subreddit", "confessions")
    title = post.get("title", "Reddit Story")
    score = post.get("score", "10.5K")
    if isinstance(score, int):
        score = f"{score/1000:.1f}k" if score >= 1000 else str(score)
    comments = post.get("num_comments", "1.2K")
    if isinstance(comments, int):
        comments = f"{comments/1000:.1f}k" if comments >= 1000 else str(comments)

    html_template = f"""
    <html lang="en">
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body {{
                background-color: transparent;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }}
            .reddit-card {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: #1A1A1B;
                border-radius: 12px;
                border: 1px solid #343536;
                padding: 20px 24px;
                color: #D7DADC;
                width: 800px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            }}
            .header {{
                display: flex;
                align-items: center;
                margin-bottom: 12px;
            }}
            .avatar {{
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background-color: #FF4500;
                display: inline-block;
                margin-right: 10px;
            }}
            .subreddit {{
                font-size: 16px;
                font-weight: 700;
                color: #D7DADC;
                margin-right: 8px;
            }}
            .author {{
                font-size: 14px;
                color: #818384;
            }}
            .title {{
                font-size: 28px;
                font-weight: 600;
                line-height: 1.3;
                margin-bottom: 16px;
                color: #F2F2F2;
            }}
            .footer {{
                display: flex;
                align-items: center;
                gap: 16px;
                color: #818384;
                font-size: 14px;
                font-weight: 700;
            }}
            .btn {{
                display: flex;
                align-items: center;
                background-color: #272729;
                padding: 8px 12px;
                border-radius: 20px;
                gap: 6px;
            }}
            .btn-icon {{
                font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <div class="reddit-card">
            <div class="header">
                <div class="avatar"></div>
                <span class="subreddit">r/{subreddit}</span>
                <span class="author">• Posted by u/anonymous</span>
            </div>
            <div class="title">{title}</div>
            <div class="footer">
                <div class="btn">
                    <span class="btn-icon">⬆️</span> {score} <span class="btn-icon">⬇️</span>
                </div>
                <div class="btn">
                    <span class="btn-icon">💬</span> {comments} Comments
                </div>
                <div class="btn">
                    <span class="btn-icon">↪️</span> Share
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    os.makedirs(output_dir, exist_ok=True)
    out_name = f"reddit_post_{post.get('id', 'demo')}.png"
    out_path = os.path.join(output_dir, out_name)
    
    # Save the screenshot directly
    hti.screenshot(html_str=html_template, save_as=out_name)
    
    # html2image saves in cwd by default, we should move it to output_dir
    if os.path.exists(out_name):
        import shutil
        shutil.move(out_name, out_path)
        
    return out_path
