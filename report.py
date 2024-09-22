import base64
from io import BytesIO
import matplotlib.pyplot as plt

def generate_html_report(figures, dataframes):
    html_content = "<html><head><title>부동산 데이터 분석 리포트</title></head><body>"
    
    for title, fig in figures.items():
        img = BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)
        img_base64 = base64.b64encode(img.getvalue()).decode()
        html_content += f"<h2>{title}</h2>"
        html_content += f'<img src="data:image/png;base64,{img_base64}" />'
    
    for title, df in dataframes.items():
        html_content += f"<h2>{title}</h2>"
        html_content += df.to_html(index=False)
    
    html_content += "</body></html>"
    return html_content

def get_download_link(html_content, filename="report.html"):
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}">다운로드 HTML 리포트</a>'
