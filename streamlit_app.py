import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from datetime import datetime
import json
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

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
        plt.bar(monthly_transactions['거래년도'].astype(str) + '-' + monthly_transactions['거래월'].astype(str),
                monthly_transactions['거래량'],
                color='#4CAF50', edgecolor='none')  # 색상 변경 및 아웃라인 제거
        plt.xlabel('연도-월', fontsize=14)
        plt.ylabel('거래량', fontsize=14)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)
        
        # 전용면적 범위별 거래량
        bins = [0, 80, 100, 120, 140, float('inf')]
        labels = ['0~80', '80~100', '100~120', '120~140', '140 이상']
        selected_data['면적 범위'] = pd.cut(selected_data['전용면적'], bins=bins, labels=labels, right=False)
        area_counts = selected_data['면적 범위'].value_counts().sort_index()
        
        # 전용면적 범위별 거래량 시각화
        st.header("전용면적 범위별 거래량 📏")
        plt.figure(figsize=(10, 6))
        plt.bar(area_counts.index, area_counts.values, color='#2196F3', edgecolor='none')  # 색상 변경 및 아웃라인 제거
        plt.xlabel('면적 범위', fontsize=14)
        plt.ylabel('거래량', fontsize=14)
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(plt)
        
        # 지역별 면적 대비 거래량 시각화
        # 지역별 면적 대비 거래량
        regional_area_counts = selected_data.groupby(['시군구']).size()
        
        # 데이터가 비어 있는 경우 처리
        if regional_area_counts.empty:
            st.write("지역별 거래량 데이터가 없습니다.")
        else:
            # 지역별 면적 대비 거래량 시각화
            st.header("지역별 면적 대비 거래량 🌍")
            plt.figure(figsize=(10, 6))
            plt.bar(regional_area_counts.index, regional_area_counts.values, color='#FFC107', edgecolor='none')  # 색상 변경 및 아웃라인 제거
            plt.xlabel('시군구', fontsize=14)
            plt.ylabel('거래량', fontsize=14)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(plt)
        
        # 거래유형 분석 시각화
        st.header("거래유형 분석 🏠")
        plt.figure(figsize=(10, 6))
        plt.pie(transaction_types, labels=transaction_types.index, autopct='%1.1f%%', startangle=140, colors=['#FF5733', '#33FF57'])  # 색상 변경
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(plt)
        
        # 거래유형 분석 표
        st.dataframe(transaction_types.reset_index().rename(columns={'index': '거래유형', 0: '거래량'}))

        # 거래량 합계
        total_volume = monthly_transactions['거래량'].sum()
        st.write(f"거래량 합계: {total_volume} 🏆")
