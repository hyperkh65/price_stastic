import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from datetime import datetime
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import base64
from io import BytesIO
from report import generate_html_report, get_download_link

# 페이지 설정을 코드 상단에 위치시킴
st.set_page_config(layout="wide")  # 여기를 추가합니다.

# Streamlit secrets에서 API 키 및 파일 경로 가져오기
service_key = st.secrets["general"]["SERVICE_KEY"]
json_file_path = "district.json"

# PublicDataReader API 서비스 키 사용
api = pdr.TransactionPrice(service_key)

# DistrictConverter 클래스 정의
class DistrictConverter:
    def __init__(self):
        self.districts = self.__read_district_file()

    def __read_district_file(self):
        with open(json_file_path, 'r') as f:
            return json.loads(f.read())

    def get_si_do_code(self, si_do_name):
        for district in self.districts:
            if si_do_name == district["si_do_name"]:
                return district["si_do_code"]

    def get_sigungu(self, si_do_code):
        for district in self.districts:
            if si_do_code == district["si_do_code"]:
                return district["sigungu"]

import base64
from io import BytesIO

import base64
from io import BytesIO

def generate_html_report(figures, dataframes):
    html_content = """
    <html>
    <head>
        <title>부동산 데이터 분석 리포트</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
            }
            h1 {
                text-align: center;
                color: #333;
            }
            h2 {
                color: #555;
            }
            .table-container {
                max-height: 400px; /* 원하는 높이 설정 */
                overflow-y: auto; /* 수직 스크롤 적용 */
                margin-bottom: 20px;
            }
            .table {
                width: 100%;
                border-collapse: collapse;
            }
            .table th, .table td {
                border: 1px solid #ddd;
                padding: 8px;
            }
            .table th {
                background-color: #f2f2f2;
                text-align: left;
            }
            .footer {
                margin-top: 40px;
                text-align: center;
                font-size: 12px;
                color: #777;
            }
            .filter {
                margin-bottom: 10px;
            }
        </style>
    </head>
    <body>
        <h1>부동산 매매가 분석 보고서</h1>
        <p>작성자: 투데이즈 (2days)</p>
        <p>연락처: <a href="mailto:hyperkh65@gmail.com">hyperkh65@gmail.com</a></p>
    """

    # 오른쪽 출력 순서에 맞춰 추가
    for title, df in dataframes.items():
        html_content += f"<h2>{title}</h2>"
        html_content += f"""
        <div class="filter">
            <input type="text" onkeyup="filterTable(this, '{title}')" placeholder="필터 입력..." />
        </div>
        <div class="table-container">
            <div class="table" id="{title}">
                {df.to_html(classes="table", border=0, escape=False)}
            </div>
        </div>
        """
    
    for title, fig in figures.items():
        img = BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)
        img_base64 = base64.b64encode(img.getvalue()).decode()
        html_content += f"<h2>{title}</h2>"
        html_content += f'<div class="graph"><img src="data:image/png;base64,{img_base64}" /></div>'
    
    # JavaScript 추가: 이미지 클릭 시 확대 표시 및 필터 기능
    html_content += """
    <script>
        document.querySelectorAll('.graph img').forEach(item => {
            item.addEventListener('click', event => {
                const img = event.target.src;
                const modal = document.createElement('div');
                modal.style.position = 'fixed';
                modal.style.left = '0';
                modal.style.top = '0';
                modal.style.width = '100%';
                modal.style.height = '100%';
                modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                modal.style.zIndex = '1000';
                const imgModal = document.createElement('img');
                imgModal.src = img;
                imgModal.style.maxWidth = '90%';
                imgModal.style.maxHeight = '90%';
                imgModal.style.position = 'absolute';
                imgModal.style.top = '50%';
                imgModal.style.left = '50%';
                imgModal.style.transform = 'translate(-50%, -50%)';
                modal.appendChild(imgModal);
                modal.addEventListener('click', () => {
                    document.body.removeChild(modal);
                });
                document.body.appendChild(modal);
            });
        });

        function filterTable(input, title) {
            const filter = input.value.toLowerCase();
            const table = document.getElementById(title);
            const rows = table.getElementsByTagName("tr");

            for (let i = 1; i < rows.length; i++) {
                const cells = rows[i].getElementsByTagName("td");
                let found = false;

                for (let j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.toLowerCase().includes(filter)) {
                        found = true;
                        break;
                    }
                }

                rows[i].style.display = found ? "" : "none";
            }
        }
    </script>
    """

    html_content += """
        <div class="footer">
            <p>이 보고서는 자동 생성되었습니다.</p>
        </div>
    </body>
    </html>
    """
    
    return html_content


# 다운로드 링크 생성 함수
def get_download_link(html_content, filename="report.html"):
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}">다운로드 HTML 리포트</a>'
      

# 사용자 입력 받기
st.title("부동산 데이터 조회")
st.sidebar.markdown("### 부동산실거래가보고서")  # 맨 위에 추가
si_do_name = st.sidebar.text_input("시/도를 입력하세요 (예: 서울특별시) 또는 '전국' 입력", "서울특별시")
start_year_month = st.sidebar.text_input("조회 시작 년월 (YYYYMM 형식, 예: 202301)", "202407")
end_year_month = st.sidebar.text_input("조회 종료 년월 (YYYYMM 형식, 예: 202312)", "202408")
data_query_button = st.sidebar.button("데이터 조회")
st.sidebar.markdown("### Made by Kimhyun ㅣ Version : 1.0")  # 맨 아래에 추가

# 폰트 파일 경로 설정
current_dir = os.getcwd()
font_path = os.path.join(current_dir, 'NanumGothicCoding.ttf')
fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'NanumGothicCoding'  # 사용자 선택한 폰트 적용

# 현재 날짜를 기준으로 기간 설정
now = datetime.now()
if not start_year_month:
    start_year_month = f"{now.year}01"
if not end_year_month:
    end_year_month = now.strftime("%Y%m")

# 진행 상황 표시
progress_text = st.sidebar.empty()
status_text = st.sidebar.empty()

if data_query_button:
    if si_do_name and start_year_month and end_year_month:
        # DistrictConverter 인스턴스 생성
        converter = DistrictConverter()

        # 데이터 수집 및 처리
        all_data = pd.DataFrame()

        if si_do_name == "전국":
            total_count = sum(len(district["sigungu"]) for district in converter.districts)
            processed_count = 0

            for district in converter.districts:
                si_do_code = district["si_do_code"]
                sigungu_list = district["sigungu"]

                for sigungu in sigungu_list:
                    sigungu_code = sigungu["sigungu_code"]
                    sigungu_name = sigungu["sigungu_name"]

                    # 현재 진행 상황 업데이트
                    processed_count += 1
                    progress_text.text(f"진행율: {100 * processed_count / total_count:.2f}% ({processed_count}/{total_count})")
                    status_text.text(f"현재 처리 중: {sigungu_name} ({sigungu_code})")

                    df = api.get_data(
                        property_type="아파트",
                        trade_type="매매",
                        sigungu_code=sigungu_code,
                        start_year_month=start_year_month,
                        end_year_month=end_year_month
                    )

                    df["sigungu_name"] = sigungu_name
                    df["si_do_name"] = district["si_do_name"]

                    all_data = pd.concat([all_data, df], ignore_index=True)
        else:
            si_do_code = converter.get_si_do_code(si_do_name)
            sigungu_list = converter.get_sigungu(si_do_code)

            total_count = len(sigungu_list)
            processed_count = 0

            for sigungu in sigungu_list:
                sigungu_code = sigungu["sigungu_code"]
                sigungu_name = sigungu["sigungu_name"]

                # 현재 진행 상황 업데이트
                processed_count += 1
                progress_text.text(f"진행율: {100 * processed_count / total_count:.2f}% ({processed_count}/{total_count})")
                status_text.text(f"현재 처리 중: {sigungu_name} ({sigungu_code})")

                df = api.get_data(
                    property_type="아파트",
                    trade_type="매매",
                    sigungu_code=sigungu_code,
                    start_year_month=start_year_month,
                    end_year_month=end_year_month
                )

                df["sigungu_name"] = sigungu_name
                df["si_do_name"] = si_do_name

                all_data = pd.concat([all_data, df], ignore_index=True)

        # 컬럼 이름 변환
        columns_to_select = {
            "si_do_name": "시도",
            "sigungu_name": "시군구",
            "umdNm": "법정동",
            "roadNm": "도로명",
            "bonbun": "지번",
            "aptNm": "아파트",
            "buildYear": "건축년도",
            "excluUseAr": "전용면적",
            "floor": "층",
            "dealYear": "거래년도",
            "dealMonth": "거래월",
            "dealDay": "거래일",
            "dealAmount": "거래금액",
            "aptSeq": "일련번호",
            "dealingGbn": "거래유형",
            "estateAgentSggNm": "중개사소재지",
            "cdealType": "해제여부",
            "cdealDay": "해제사유발생일"
        }

        selected_data = all_data.rename(columns=columns_to_select)[list(columns_to_select.values())]

        # 데이터 표로 표시
        st.write("### 조회 결과")
        st.dataframe(selected_data)

        # 분석 자료
        st.write("### 분석 자료")
        total_transactions = selected_data.shape[0]
        st.write(f"총 거래량: {total_transactions}")

        # 전용면적 데이터 타입 변환 및 결측치 처리
        selected_data['전용면적'] = pd.to_numeric(selected_data['전용면적'], errors='coerce')
        selected_data.dropna(subset=['전용면적'], inplace=True)  # 결측치 삭제

        # 매월 거래량
        monthly_transactions = selected_data.groupby(['거래년도', '거래월']).size().reset_index(name='거래량')
        
        # 매월 거래량 시각화
        st.header("매월 거래량 📅")
        fig_monthly = plt.figure(figsize=(10, 6))
        plt.bar(monthly_transactions['거래년도'].astype(str) + '-' + monthly_transactions['거래월'].astype(str), monthly_transactions['거래량'], color='skyblue')
        plt.xlabel('연도-월', fontsize=14)
        plt.ylabel('거래량', fontsize=14)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig_monthly)
        
        # 매월 거래량 표 추가
        monthly_summary = monthly_transactions.groupby('거래년도')['거래량'].sum().reset_index()
        monthly_summary.columns = ['거래년도', '월별 거래량']
        st.dataframe(monthly_transactions)
        
        # 지역별 거래량
        regional_summary = selected_data.groupby('시군구').size().reset_index(name='거래량')
        regional_summary['총계'] = regional_summary['거래량'].sum()  # 총계 열 추가
    
        # 전용면적 범위별 거래량
        bins = [0, 80, 100, 120, 140, float('inf')]
        labels = ['0~80', '80~100', '100~120', '120~140', '140 이상']
        selected_data['면적 범위'] = pd.cut(selected_data['전용면적'], bins=bins, labels=labels, right=False)
        area_counts = selected_data['면적 범위'].value_counts().sort_index()
        
        # 전용면적 범위별 거래량 시각화
        st.header("전용면적 범위별 거래량 📏")
        fig_area = plt.figure(figsize=(10, 6))
        plt.bar(area_counts.index, area_counts.values, color='#2196F3', edgecolor='none')  # 색상 변경 및 아웃라인 제거
        plt.xlabel('면적 범위', fontsize=14)
        plt.ylabel('거래량', fontsize=14)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig_area)
        
        # 전용면적 범위별 거래량 표 추가
        area_summary = area_counts.reset_index()
        area_summary.columns = ['면적 범위', '거래량']
        area_summary['총계'] = area_summary['거래량'].sum()  # 총계 열 추가
        st.dataframe(area_summary)
        
        # 지역별 면적 대비 거래량
        regional_area_counts = selected_data.groupby(['시군구']).size()
        
        # 데이터가 비어 있는 경우 처리
        if regional_area_counts.empty:
            st.write("지역별 거래량 데이터가 없습니다.")
        else:
            # 지역별 면적 대비 거래량 시각화
            st.header("지역별 면적 대비 거래량 🌍")
            fig_regional = plt.figure(figsize=(10, 6))
            plt.bar(regional_area_counts.index, regional_area_counts.values, color='#FFC107', edgecolor='none')  # 색상 변경 및 아웃라인 제거
            plt.xlabel('시군구', fontsize=14)
            plt.ylabel('거래량', fontsize=14)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig_regional)
        
            # 지역별 면적 대비 거래량 표 추가
            regional_summary = regional_area_counts.reset_index()
            regional_summary.columns = ['시군구', '거래량']
            regional_summary['총계'] = regional_summary['거래량'].sum()  # 총계 열 추가
            st.dataframe(regional_summary)
        
        # 거래유형 분석
        transaction_types = selected_data['거래유형'].value_counts()
        
        # 데이터가 비어 있는 경우 처리
        if transaction_types.empty:
            st.write("거래유형 데이터가 없습니다.")
        else:
            # 거래유형 분석 시각화
            st.header("거래유형 분석 🏠")
            fig_types = plt.figure(figsize=(10, 6))
            plt.pie(transaction_types, labels=transaction_types.index, autopct='%1.1f%%', startangle=140, colors=['#FF5733', '#33FF57'])  # 색상 변경
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            st.pyplot(fig_types)
        
        # 거래유형 분석 표
        st.dataframe(transaction_types.reset_index().rename(columns={'index': '거래유형', 0: '거래량'}))

        # 거래량 합계
        total_volume = monthly_transactions['거래량'].sum()
        st.write(f"거래량 합계: {total_volume} 🏆")
        
        popular_apartments = selected_data.groupby(['법정동', '아파트']).size().reset_index(name='거래량')
        
        # 각 법정동별 거래량이 가장 높은 아파트 찾기
        top_apartments = popular_apartments.loc[popular_apartments.groupby('법정동')['거래량'].idxmax()]
        
        # 결과를 표로 표시
        st.header("법정동별 거래 빈도가 높은 아파트 🌍")
        st.dataframe(top_apartments)

        # 모든 그림과 데이터프레임 저장
        figures = {
            "매월 거래량": fig_monthly,
            "전용면적 범위별 거래량": fig_area,
            "지역별 면적 대비 거래량": fig_regional,
            "거래유형 분석": fig_types
        }
        
        dataframes = {
            "조회 결과": selected_data,
            "매월 거래량": monthly_transactions,
            "전용면적 범위별 거래량": area_summary,
            "지역별 면적 대비 거래량": regional_summary,
            "거래유형 분석": transaction_types.reset_index().rename(columns={'index': '거래유형', 0: '거래량'}),
            "법정동별 거래 빈도가 높은 아파트": top_apartments
        }

      # HTML 리포트 생성
        html_report = generate_html_report(figures, dataframes)
        
        # HTML 리포트를 파일로 저장
        with open("report.html", "w", encoding="utf-8") as f:
            f.write(html_report)
        
        # 다운로드 링크 생성
        def get_download_link(filename="report.html"):
            with open(filename, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<a href="data:file/html;base64,{b64}" download="{filename}">다운로드 HTML 리포트</a>'
        
        # 다운로드 링크 표시
        st.sidebar.markdown(get_download_link("report.html"), unsafe_allow_html=True)

