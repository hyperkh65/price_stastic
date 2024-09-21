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
        with open(json_file_path, 'r', encoding='utf-8') as f:
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

# 진행현황과 데이터 조회 버튼
st.sidebar.header("진행현황")
progress_text = st.sidebar.empty()

if st.sidebar.button("데이터 조회"):
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

                    # 진행현황 업데이트
                    progress_text.text(f"현재 검색 중: {sigungu_name} ({sigungu_code})")

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

                # 진행현황 업데이트
                progress_text.text(f"현재 검색 중: {sigungu_name} ({sigungu_code})")

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

        # 전용면적 처리
        all_data = all_data[all_data['excluUseAr'].notna()]  # 결측치 제외
        all_data['excluUseAr'] = all_data['excluUseAr'].astype(float)  # 소수점 처리

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
        st.dataframe(selected_data.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        # 분석 자료 생성
        total_count = selected_data.shape[0]
        monthly_count = selected_data.groupby(['거래년도', '거래월']).size().reset_index(name='거래량')
        region_count = selected_data['시군구'].value_counts().reset_index()
        region_count.columns = ['시군구', '거래량']
        transaction_type_count = selected_data['거래유형'].value_counts().reset_index()
        transaction_type_count.columns = ['거래유형', '거래량']
        area_bins = [0, 60, 85, 100, 120, 140, 160, float('inf')]
        area_labels = ['60㎡ 이하', '60㎡~85㎡', '85㎡~100㎡', '100㎡~120㎡', '120㎡~140㎡', '140㎡~160㎡', '160㎡ 초과']
        selected_data['평형대'] = pd.cut(selected_data['전용면적'], bins=area_bins, labels=area_labels, right=False)
        area_count = selected_data['평형대'].value_counts().reset_index()
        area_count.columns = ['평형대', '거래량']
        amount_bins = [0, 300000000, 500000000, 700000000, 900000000, 1100000000, float('inf')]
        amount_labels = ['300만원 이하', '300만원~500만원', '500만원~700만원', '700만원~900만원', '900만원~1100만원', '1100만원 초과']
        selected_data['금액대'] = pd.cut(selected_data['거래금액'], bins=amount_bins, labels=amount_labels, right=False)
        amount_count = selected_data['금액대'].value_counts().reset_index()
        amount_count.columns = ['금액대', '거래량']

        # 총 거래량 표시
        st.write(f"### 총 거래량: {total_count}건")

        # 매월 거래량 시각화
        st.write("### 매월 거래량")
        plt.figure(figsize=(10, 5))
        plt.plot(monthly_count['거래년도'].astype(str) + '-' + monthly_count['거래월'].astype(str), monthly_count['거래량'], marker='o')
        plt.title('매월 거래량')
        plt.xlabel('년도-월')
        plt.ylabel('거래량')
        plt.xticks(rotation=45)
        st.pyplot(plt)

        # 지역별 거래량 시각화
        st.write("### 지역별 거래량")
        plt.figure(figsize=(10, 5))
        plt.bar(region_count['시군구'], region_count['거래량'], color='skyblue')
        plt.title('지역별 거래량')
        plt.xlabel('시군구')
        plt.ylabel('거래량')
        plt.xticks(rotation=45)
        st.pyplot(plt)

        # 거래유형 분석 시각화
        st.write("### 거래유형 분석")
        plt.figure(figsize=(10, 5))
        plt.pie(transaction_type_count['거래량'], labels=transaction_type_count['거래유형'], autopct='%1.1f%%', startangle=140)
        plt.title('거래유형 비율')
        st.pyplot(plt)

        # 평형대별 거래량 시각화
        st.write("### 평형대별 거래량")
        plt.figure(figsize=(10, 5))
        plt.bar(area_count['평형대'], area_count['거래량'], color='salmon')
        plt.title('평형대별 거래량')
        plt.xlabel('평형대')
        plt.ylabel('거래량')
        plt.xticks(rotation=45)
        st.pyplot(plt)

        # 금액대별 거래량 시각화
        st.write("### 금액대별 거래량")
                plt.figure(figsize=(10, 5))
        plt.bar(amount_count['금액대'], amount_count['거래량'], color='lightgreen')
        plt.title('금액대별 거래량')
        plt.xlabel('금액대')
        plt.ylabel('거래량')
        plt.xticks(rotation=45)
        st.pyplot(plt)

        # 분석 결과를 표로 표시
        st.write("### 분석 자료")

        st.write("#### 매월 거래량")
        st.dataframe(monthly_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        st.write("#### 지역별 거래량")
        st.dataframe(region_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        st.write("#### 거래유형 분석")
        st.dataframe(transaction_type_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        st.write("#### 평형대별 거래량")
        st.dataframe(area_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))

        st.write("#### 금액대별 거래량")
        st.dataframe(amount_count.style.set_table_attributes('style="color: black; background-color: #f5f5f5;"'))
