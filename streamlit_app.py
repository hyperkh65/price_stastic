import streamlit as st
import pandas as pd
import json
import PublicDataReader as pdr
from PublicDataReader import TransactionPrice
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import folium

# PublicDataReader API 서비스 키
service_key = st.secrets["SERVICE_KEY"]
api = pdr.TransactionPrice(service_key)

class DistrictConverter:
    def __init__(self):
        self.districts = self.__read_district_file()

    def __read_district_file(self):
        json_file_path = 'district.json'  # 최상위 폴더에 위치
        with open(json_file_path, 'r') as f:
            return json.load(f)

    def get_si_do_code(self, si_do_name):
        for district in self.districts:
            if si_do_name == district["si_do_name"]:
                return district["si_do_code"]

    def get_sigungu(self, si_do_code):
        for district in self.districts:
            if si_do_code == district["si_do_code"]:
                return district["sigungu"]

def load_data(si_do_name, start_year_month, end_year_month):
    converter = DistrictConverter()
    all_data = pd.DataFrame()

    if si_do_name == "전국":
        for district in converter.districts:
            si_do_code = district["si_do_code"]
            sigungu_list = district["sigungu"]
            for sigungu in sigungu_list:
                sigungu_code = sigungu["sigungu_code"]
                sigungu_name = sigungu["sigungu_name"]

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

    return all_data

# Streamlit UI
st.title("부동산 데이터 분석")
si_do_name = st.selectbox("시/도를 선택하세요:", ["전국", "서울특별시", "부산광역시", "대구광역시"])
start_year_month = st.text_input("조회 시작 년월 (YYYYMM 형식, 예: 202301):")
end_year_month = st.text_input("조회 종료 년월 (YYYYMM 형식, 예: 202312):")

if st.button("조회 시작"):
    data = load_data(si_do_name, start_year_month, end_year_month)
    if not data.empty:
        st.write(data)

        # 시각화: 거래금액 히스토그램
        plt.figure(figsize=(10, 5))
        sns.histplot(data['dealAmount'], bins=30)
        plt.title("거래금액 분포")
        plt.xlabel("거래금액")
        plt.ylabel("빈도수")
        st.pyplot(plt)

        # 시각화: 지도의 시각화
        if 'lat' in data.columns and 'lon' in data.columns:
            m = folium.Map(location=[data['lat'].mean(), data['lon'].mean()], zoom_start=12)
            for idx, row in data.iterrows():
                folium.CircleMarker(
                    location=(row['lat'], row['lon']),
                    radius=5,
                    color='blue',
                    fill=True,
                    fill_color='blue',
                    fill_opacity=0.6
                ).add_to(m)
            st.write(m)

        # 데이터 다운로드
        csv = data.to_csv(index=False).encode('utf-8')
        st.download_button("CSV로 다운로드", csv, "data.csv", "text/csv")

        excel_output = f"{si_do_name}_{start_year_month}_{end_year_month}.xlsx"
        data.to_excel(excel_output, index=False, engine='xlsxwriter')
        st.download_button("Excel로 다운로드", excel_output, "data.xlsx")
    else:
        st.error("데이터가 없습니다.")
