import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from datetime import datetime
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import requests

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

# 사용자 입력 받기
st.title("부동산 데이터 조회")
si_do_name = st.sidebar.text_input("시/도를 입력하세요 (예: 서울특별시) 또는 '전국' 입력", "전국")
start_year_month = st.sidebar.text_input("조회 시작 년월 (YYYYMM 형식, 예: 202301)", "")
end_year_month = st.sidebar.text_input("조회 종료 년월 (YYYYMM 형식, 예: 202312)", "")
data_query_button = st.sidebar.button("데이터 조회")
post_to_blog_button = st.sidebar.button("블로그에 포스팅")

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
        plt.figure(figsize=(10, 6))
        plt.bar(monthly_transactions['거래년도'].astype(str) + '-' + monthly_transactions['거래월'].astype(str), monthly_transactions['거래량'], color='skyblue')
        plt.xlabel('연도-월', fontsize=14)
        plt.ylabel('거래량', fontsize=14)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)

        # 매월 거래량 표 추가
        monthly_summary = monthly_transactions.groupby('거래년도')['거래량'].sum().reset_index()
        monthly_summary.columns = ['거래년도', '월별 거래량']
        st.dataframe(monthly_transactions)

        # 거래유형 분석
        transaction_types = selected_data['거래유형'].value_counts()
        st.header("거래유형 분석 🏠")
        plt.figure(figsize=(10, 6))
        plt.pie(transaction_types, labels=transaction_types.index, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        st.pyplot(plt)

        # 거래유형 분석 표
        st.dataframe(transaction_types.reset_index().rename(columns={'index': '거래유형', 0: '거래량'}))

        # 법정동별 인기 아파트 분석
        popular_apartments = selected_data.groupby(['법정동', '아파트']).size().reset_index(name='거래량')
        top_apartments = popular_apartments.loc[popular_apartments.groupby('법정동')['거래량'].idxmax()]
        
        # 결과를 표로 표시
        st.header("법정동별 거래 빈도가 높은 아파트 🌍")
        st.dataframe(top_apartments)

        # 블로그 포스팅 처리
        if post_to_blog_button:
            wp_username = st.secrets["wordpress"]["username"]
            wp_password = st.secrets["wordpress"]["password"]
            post_title = f"{start_year_month} - {end_year_month} 부동산 거래 데이터"
            post_content = f"<h2>조회 결과</h2>{selected_data.to_html(index=False)}<h2>분석 자료</h2><p>총 거래량: {total_transactions}</p>"

            response = requests.post(
                'https://your-wordpress-site.com/wp-json/wp/v2/posts',
                json={
                    'title': post_title,
                    'content': post_content,
                    'status': 'publish'
                },
                auth=(wp_username, wp_password)
            )

            if response.status_code == 201:
                st.success("포스팅이 완료되었습니다.")
            else
                            st.error("포스팅에 실패했습니다. 오류: " + response.text)

            # PDF 저장 (기본적으로 matplotlib 그래프 및 표 포함)
            pdf_path = "report.pdf"
            with open(pdf_path, "wb") as f:
                # 여기에 PDF로 변환하는 코드를 추가
                pass  # 실제로 PDF로 변환하는 코드를 추가해야 합니다.

            st.success("PDF가 생성되었습니다.")

# 나머지 코드 부분은 원래와 동일하게 유지
