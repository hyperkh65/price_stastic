import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from datetime import datetime
import json
import matplotlib.pyplot as plt
import seaborn as sns

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

        # 매월 거래량
        monthly_transactions = selected_data.groupby(['거래년도', '거래월']).size().reset_index(name='거래량')
        st.write("매월 거래량")
        monthly_fig, ax = plt.subplots()
        sns.lineplot(data=monthly_transactions, x='거래월', y='거래량', hue='거래년도', ax=ax)
        st.pyplot(monthly_fig)
        st.dataframe(monthly_transactions)

        # 지역별 거래량
        regional_transactions = selected_data['시군구'].value_counts().reset_index()
        regional_transactions.columns = ['시군구', '거래량']
        st.write("지역별 거래량")
        regional_fig, ax = plt.subplots()
        sns.barplot(data=regional_transactions, x='시군구', y='거래량', ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(regional_fig)
        st.dataframe(regional_transactions)

        # 거래유형 분석
        transaction_type = selected_data['거래유형'].value_counts().reset_index()
        transaction_type.columns = ['거래유형', '거래량']
        st.write("거래유형 분석")
        transaction_type_fig, ax = plt.subplots()
        ax.pie(transaction_type['거래량'], labels=transaction_type['거래유형'], autopct='%1.1f%%', startangle=90)
        st.pyplot(transaction_type_fig)
        st.dataframe(transaction_type)

        # 평형대별 거래량
        area_bins = [0, 30, 50, 70, 100, 130, 150, 200, 300]
        area_labels = ['0-30', '31-50', '51-70', '71-100', '101-130', '131-150', '151-200', '200+']
        selected_data['평형대'] = pd.cut(selected_data['전용면적'], bins=area_bins, labels=area_labels, right=False)
        area_transactions = selected_data['평형대'].value_counts().reset_index()
        area_transactions.columns = ['평형대', '거래량']
        st.write("평형대별 거래량")
        area_fig, ax = plt.subplots()
        sns.barplot(data=area_transactions, x='평형대', y='거래량', ax=ax)
        st.pyplot(area_fig)
        st.dataframe(area_transactions)

        # 금액대별 거래량
        price_bins = [0, 30000, 60000, 90000, 120000, 150000, 200000, 300000]
        price_labels = ['0-30M', '31-60M', '61-90M', '91-120M', '121-150M', '151-200M', '200M+']
        selected_data['금액대'] = pd.cut(selected_data['거래금액'] / 10000, bins=price_bins, labels=price_labels, right=False)
        price_transactions = selected_data['금액대'].value_counts().reset_index()
        price_transactions.columns = ['금액대', '거래량']
        st.write("금액대별 거래량")
        price_fig, ax = plt.subplots()
        sns.barplot(data=price_transactions, x='금액대', y='거래량', ax=ax)
        st.pyplot(price_fig)
        st.dataframe(price_transactions)

    else:
        st.error("모든 필드를 채워주세요.")
