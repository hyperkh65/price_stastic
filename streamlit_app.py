import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from datetime import datetime
import json
from io import BytesIO
import matplotlib.pyplot as plt

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
si_do_name = st.text_input("시/도를 입력하세요 (예: 서울특별시) 또는 '전국' 입력", "전국")
start_year_month = st.text_input("조회 시작 년월 (YYYYMM 형식, 예: 202301)", "")
end_year_month = st.text_input("조회 종료 년월 (YYYYMM 형식, 예: 202312)", "")

# 현재 날짜를 기준으로 기간 설정
now = datetime.now()
if not start_year_month:
    start_year_month = f"{now.year}01"
if not end_year_month:
    end_year_month = now.strftime("%Y%m")

# 데이터 조회 버튼 추가
if st.button("데이터 조회"):
    if si_do_name and start_year_month and end_year_month:
        # DistrictConverter 인스턴스 생성
        converter = DistrictConverter()

        # 데이터 수집 및 처리
        all_data = pd.DataFrame()

        if si_do_name == "전국":
            for district in converter.districts:
                si_do_code = district["si_do_code"]
                sigungu_list = district["sigungu"]
                for sigungu in sigungu_list:
                    sigungu_code = sigungu["sigungu_code"]
                    sigungu_name = sigungu["sigungu_name"]

                    st.write(f"Processing data for {sigungu_name} ({sigungu_code})")

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

            for sigungu in sigungu_list:
                sigungu_code = sigungu["sigungu_code"]
                sigungu_name = sigungu["sigungu_name"]

                st.write(f"Processing data for {sigungu_name} ({sigungu_code})")

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

        # 총 거래량
        total_transactions = selected_data.shape[0]
        st.write(f"### 총 거래량: {total_transactions}")

        # 매월 거래량
        monthly_count = selected_data.groupby(['거래년도', '거래월']).size().reset_index(name='거래량')
        plt.figure(figsize=(10, 5))
        plt.plot(monthly_count['거래월'].astype(str) + '-' + monthly_count['거래년도'].astype(str), monthly_count['거래량'], marker='o')
        plt.title('매월 거래량')
        plt.xlabel('거래 월')
        plt.ylabel('거래량')
        plt.xticks(rotation=45)
        st.pyplot(plt)
        st.dataframe(monthly_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        # 지역별 거래량
        region_count = selected_data['시군구'].value_counts().reset_index()
        region_count.columns = ['시군구', '거래량']
        plt.figure(figsize=(10, 5))
        plt.bar(region_count['시군구'], region_count['거래량'], color='lightblue')
        plt.title('지역별 거래량')
        plt.xlabel('시군구')
        plt.ylabel('거래량')
        plt.xticks(rotation=45)
        st.pyplot(plt)
        st.dataframe(region_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        # 거래유형 분석
        transaction_type_count = selected_data['거래유형'].value_counts().reset_index()
        transaction_type_count.columns = ['거래유형', '거래량']
        plt.figure(figsize=(6, 6))
        plt.pie(transaction_type_count['거래량'], labels=transaction_type_count['거래유형'], autopct='%1.1f%%')
        plt.title('거래유형 분석')
        st.pyplot(plt)
        st.dataframe(transaction_type_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        # 평형대별 거래량
        selected_data['평형대'] = pd.cut(selected_data['전용면적'], bins=[0, 60, 85, 100, 120, 150, 200], labels=['60㎡ 이하', '60~85㎡', '85~100㎡', '100~120㎡', '120~150㎡', '150㎡ 이상'], right=False)
        area_count = selected_data['평형대'].value_counts().reset_index()
        area_count.columns = ['평형대', '거래량']
        plt.figure(figsize=(10, 5))
        plt.bar(area_count['평형대'], area_count['거래량'], color='salmon')
        plt.title('평형대별 거래량')
        plt.xlabel('평형대')
        plt.ylabel('거래량')
        st.pyplot(plt)
        st.dataframe(area_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        # 금액대별 거래량
        selected_data['금액대'] = pd.cut(selected_data['거래금액'], bins=[0, 30000, 60000, 90000, 120000, 150000, 180000, 210000, 240000, 270000, 300000], labels=['30백만원 이하', '30~60백만원', '60~90백만원', '90~120백만원', '120~150백만원', '150~180백만원', '180~210백만원', '210~240백만원', '240~270백만원', '270~300백만원'], right=False)
        amount_count = selected_data['금액대'].value_counts().reset_index()
        amount_count.columns = ['금액대', '거래량']
        plt.figure(figsize=(10, 5))
        plt.bar(amount_count['금액대'], amount_count['거래량'], color='lightgreen')
        plt.title('금액대별 거래량')
        plt.xlabel('금액대')
        plt.ylabel('거래량')
        plt.xticks(rotation=45)
        st.pyplot(plt)
        st.dataframe(amount_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

# 진행현황 고정탭 추가
with st.sidebar:
    st.write(f"현재 검색 지역: {si_do_name}")
    progress = (all_data.shape[0] / total_transactions) * 100 if total_transactions
        if total_transactions > 0 else 0
    st.write(f"진행율: {progress:.2f}% ({all_data.shape[0]}/{total_transactions})")

# 진행현황 표시
st.sidebar.progress(progress)

# UTF-8 인코딩 처리 (표시 관련)
pd.options.display.encoding = 'utf-8'
