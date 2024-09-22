import base64
from io import BytesIO

def generate_html_report(figures, dataframes):
    html_content = """
    <html>
        <head>
            <title>부동산 데이터 분석 리포트</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h2 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin: 10px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                img { max-width: 100%; height: auto; }
            </style>
        </head>
        <body>
    """
    
    for title, fig in figures.items():
        img = BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)
        img_base64 = base64.b64encode(img.getvalue()).decode()
        html_content += f"<h2>{title}</h2>"
        html_content += f'<img src="data:image/png;base64,{img_base64}" />'
    
    for title, df in dataframes.items():
        html_content += f"<h2>{title}</h2>"
        html_content += df.to_html(index=False, border=0)  # border를 0으로 설정하여 테두리 제거
    
    html_content += """
        </body>
    </html>
    """
    return html_content

def get_download_link(html_content, filename="report.html"):
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}">다운로드 HTML 리포트</a>'
