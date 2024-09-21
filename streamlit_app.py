import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from datetime import datetime
import json
import matplotlib.pyplot as plt
from io import BytesIO

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
st.title("Real Estate Data Analysis")
si_do_name = st.sidebar.text_input("Enter city/province (e.g., Seoul) or 'All'", "All")
start_year_month = st.sidebar.text_input("Start Year-Month (YYYYMM format, e.g., 202301)", "")
end_year_month = st.sidebar.text_input("End Year-Month (YYYYMM format, e.g., 202312)", "")
data_query_button = st.sidebar.button("Query Data")

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

        if si_do_name == "All":
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
                    progress_text.text(f"Progress: {100 * processed_count / total_count:.2f}% ({processed_count}/{total_count})")
                    status_text.text(f"Processing: {sigungu_name} ({sigungu_code})")

                    df = api.get_data(
                        property_type="Apartment",
                        trade_type="Sale",
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
                progress_text.text(f"Progress: {100 * processed_count / total_count:.2f}% ({processed_count}/{total_count})")
                status_text.text(f"Processing: {sigungu_name} ({sigungu_code})")

                df = api.get_data(
                    property_type="Apartment",
                    trade_type="Sale",
                    sigungu_code=sigungu_code,
                    start_year_month=start_year_month,
                    end_year_month=end_year_month
                )

                df["sigungu_name"] = sigungu_name
                df["si_do_name"] = si_do_name

                all_data = pd.concat([all_data, df], ignore_index=True)

        # 컬럼 이름 변환
        columns_to_select = {
            "si_do_name": "City/Province",
            "sigungu_name": "District",
            "umdNm": "LegalTown",
            "roadNm": "Street",
            "bonbun": "LandNumber",
            "aptNm": "Apartment",
            "buildYear": "BuildYear",
            "excluUseAr": "Area(m²)",
            "floor": "Floor",
            "dealYear": "Year",
            "dealMonth": "Month",
            "dealDay": "Day",
            "dealAmount": "Price",
            "aptSeq": "Sequence",
            "dealingGbn": "TransactionType",
            "estateAgentSggNm": "AgentLocation",
            "cdealType": "Cancellation",
            "cdealDay": "CancellationDate"
        }

        selected_data = all_data.rename(columns=columns_to_select)[list(columns_to_select.values())]

        # 데이터 표로 표시
        st.write("### Query Results")
        st.dataframe(selected_data)

        # 분석 자료
        st.write("### Analysis Data")
        total_transactions = selected_data.shape[0]
        st.write(f"Total Transactions: {total_transactions}")

        # 매월 거래량
        monthly_transactions = selected_data.groupby(['Year', 'Month']).size().reset_index(name='Transactions')
        st.write("Monthly Transactions")
        st.dataframe(monthly_transactions)
        fig, ax = plt.subplots()
        ax.plot(monthly_transactions['Year'].astype(str) + '-' + monthly_transactions['Month'].astype(str), monthly_transactions['Transactions'], marker='o')
        ax.set_xlabel("Year-Month")
        ax.set_ylabel("Number of Transactions")
        ax.set_title("Monthly Transactions")
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # 지역별 거래량
        regional_transactions = selected_data.groupby(['Year', 'Month', 'District']).size().reset_index(name='Transactions')
        st.write("Monthly Regional Transactions")
        st.dataframe(regional_transactions)

        # 지역별 거래 비중
        region_summary = selected_data['District'].value_counts(normalize=True).reset_index()
        region_summary.columns = ['District', 'Proportion']
        st.write("Regional Transaction Proportion")
        fig, ax = plt.subplots()
        ax.pie(region_summary['Proportion'], labels=region_summary['District'], autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        st.pyplot(fig)

    else:
        st.error("Please fill in all fields.")
