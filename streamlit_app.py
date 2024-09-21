import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium.plugins import HeatMap
import PublicDataReader as pdr
from PublicDataReader import TransactionPrice
from datetime import datetime

# PublicDataReader API 서비스 키
service_key = st.secrets["SERVICE_KEY"]
api = pdr.TransactionPrice(service_key)

# 구글 드라이브에 데이터 저장 대신 데이터 프레임 사용
class DistrictConverter:
    def __init__(self):
        self.districts = self.__read_district_file()

    def __read_district_file(self):
        with open('district.json', 'r') as f:
            return json.load(f)

    def get_si_do_code(self, si_do_name):
        for district in self.districts:
            if si_do_name == district["si_do_name"]:
                return district["si_do_code"]

    def get_sigungu(self, si_do_code):
        for district in self.districts:
            if si_do_code == district["si_do_code"]:
                return district["sigungu"]

# 사용자 입력 함수
def get_user_input():
    si_do_name = st.text_input("시/도를 입력하세요 (예: 서울특별시) 또는 '전국' 입력: ", "전국")
    start_year_month = st.text_input("조회 시작 년월 (YYYYMM 형식, 예: 202301): ")
    end_year_month = st.text_input("조회 종료 년월 (YYYYMM 형식, 예: 202312): ")

    return si_do_name, start_year_month, end_year_month

# 데이터 로드 함수
def load_data(si_do_name, start_year_month, end_year_month):
    now = datetime.now()
    current_year_month = now.strftime("%Y%m")

    if not start_year_month:
        start_year_month = f"{now.year}01"
    if not end_year_month:
        end_year_month = current_year_month

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

# 시각화 함수
def plot_histogram(data):
    plt.figure(figsize=(10, 6))
    sns.histplot(data['거래금액'], bins=30, kde=True)
    plt.title('매매가 분포')
    plt.xlabel('매매가')
    plt.ylabel('거래 수')
    st.pyplot(plt)

def plot_boxplot(data):
    plt.figure(figsize=(10, 6))
    sns.boxplot(x='sigungu_name', y='거래금액', data=data)
    plt.title('지역별 매매가 상자 수염 그림')
    plt.xticks(rotation=45)
    st.pyplot(plt)

def plot_time_series(data):
    data['거래일'] = pd.to_datetime(data['거래일'])
    monthly_data = data.resample('M', on='거래일').mean()
    plt.figure(figsize=(10, 6))
    plt.plot(monthly_data.index, monthly_data['거래금액'])
    plt.title('월별 평균 매매가')
    plt.xlabel('날짜')
    plt.ylabel('매매가')
    st.pyplot(plt)

def plot_scatter(data):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='전용면적', y='거래금액', data=data)
    plt.title('전용면적과 매매가의 관계')
    plt.xlabel('전용면적')
    plt.ylabel('매매가')
    st.pyplot(plt)

def plot_map(data):
    m = folium.Map(location=[35.5, 128.0], zoom_start=7)
    heat_data = [[row['위도'], row['경도'], row['거래금액']] for index, row in data.iterrows()]
    HeatMap(heat_data).add_to(m)
    st.write(m)

# Streamlit 앱 설정
st.title('부동산 매매가 분석')
si_do_name, start_year_month, end_year_month = get_user_input()

if st.button("데이터 조회"):
    data = load_data(si_do_name, start_year_month, end_year_month)
    
    if data.empty:
        st.error("데이터를 로드할 수 없습니다.")
    else:
        st.subheader('시각화 결과')
        plot_histogram(data)
        plot_boxplot(data)
        plot_time_series(data)
        plot_scatter(data)
        plot_map(data)

        # 데이터 다운로드 옵션
        if st.button('엑셀로 다운로드'):
            output_file = "부동산_매매가_데이터.xlsx"
            data.to_excel(output_file, index=False)
            st.success(f"{output_file}로 다운로드 되었습니다.")
