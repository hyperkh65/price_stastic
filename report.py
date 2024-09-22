import base64
from io import BytesIO

def generate_html_report(figures, dataframes):
    html_content = """
    <html>
        <head>
            <title>부동산 데이터 분석 리포트</title>
        </head>
        <body>
            <h1>부동산 데이터 분석 리포트</h1>
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
        html_content += df.to_html(index=False)
    
    html_content += """
        </body>
    </html>
    """
    return html_content
