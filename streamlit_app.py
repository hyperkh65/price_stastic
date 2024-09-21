import streamlit as st
import pandas as pd
import json
import time
import folium
import matplotlib.pyplot as plt
import seaborn as sns

# JSON 파일 경로 설정
JSON_FILE_PATH = 'district.json'

# 지역 코드 변환 클래스
class DistrictConverter:
    def __init__(self):
        self.districts = self.__read_district_file()

    def __read_district_file(self):
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_si_do_code(self, si_do_name):
        for district in self.districts:
            if si_do_name == district["si_do_name"]:
                return district["si_do_code"]
    
    def get_sigungu(self, si_do_code):
        for district in self.districts:
            if si_do_code == district["si_do_code"]:
                return district["sigungu"]

# 데이터 로드 함수 (예시로 간단한 더미 데이터 사용)
def load_data(si_do_name, start_year_month, end_year_month):
    # 여기에 데이터 로드 로직을 추가해야 합니다.
    # 현재는 빈 데이터프레임으로 초기화
    data = {
        'sigungu_name': ['강남구', '송파구', '강서구'] * 10,
        'dealAmount': [30000 + i * 1000 for i in range(30)],
        'excluUseAr': [50 + i for i in range(30)],
        'dealYear': [2023] * 30,
        'dealMonth': [i % 12 + 1 for i in range(30)],
        'latitude': [37.5172, 37.5144, 37.5512] * 10,
        'longitude': [127.0473, 127.1067, 126.8497] * 10
    }
    return pd.DataFrame(data)

# 시각화 함수
def visualize_data(data):
    # 히스토그램
    st.subheader("매매가 분포 히스토그램")
    plt.figure(figsize=(10, 5))
    sns.histplot(data['dealAmount'], kde=True)
    st.pyplot(plt)

    # 상자 수염 그림
    st.subheader("지역별 매매가 상자 수염 그림")
    plt.figure(figsize=(10, 5))
    sns.boxplot(x='sigungu_name', y='dealAmount', data=data)
    plt.xticks(rotation=45)
    st.pyplot(plt)

    # 시간 시리즈 그래프
    data['date'] = pd.to_datetime(data[['dealYear', 'dealMonth']].astype(str).agg('-'.join, axis=1))
    monthly_avg = data.groupby(data['date'].dt.to_period('M')).mean()
    st.subheader("월별 평균 매매가")
    plt.figure(figsize=(10, 5))
    plt.plot(monthly_avg.index.astype(str), monthly_avg['dealAmount'])
    plt.xticks(rotation=45)
    st.pyplot(plt)

    # 산점도
    st.subheader("전용면적과 매매가 산점도")
    plt.figure(figsize=(10, 5))
    sns.scatterplot(x='excluUseAr', y='dealAmount', data=data)
    st.pyplot(plt)

    # 지도 시각화
    st.subheader("거래 금액 히트맵")
    m = folium.Map(location=[37.5665, 126.978], zoom_start=10)
    for idx, row in data.iterrows():
        folium.CircleMarker(location=[row['latitude'], row['longitude']],
                            radius=row['dealAmount'] / 5000,
                            color='blue', fill=True).add_to(m)
    st.components.v1.html(m._repr_html_(), width=700, height=500)

# Streamlit 앱 시작
st.title("부동산 매매 데이터 분석")
si_do_name = st.selectbox("시/도 선택:", options=["서울특별시", "전국"])
start_year_month = st.text_input("조회 시작 년월 (YYYYMM):", "202301")
end_year_month = st.text_input("조회 종료 년월 (YYYYMM):", "202312")

if st.button("조회 시작"):
    # 데이터 로드 및 시각화
    with st.spinner("데이터를 불러오는 중입니다..."):
        data = load_data(si_do_name, start_year_month, end_year_month)
        time.sleep(1)  # 데이터 로드 지연
        visualize_data(data)

    # 진행 상태 표시
    st.write("현재 검토 중인 지역:", si_do_name)
    st.write("진행률: 100%")
    st.write("진행한 검사 수: 1")
    st.write("남은 검사 수: 0")

    # 데이터 다운로드
    output = data.to_csv(index=False, encoding='utf-8')  # CSV로 저장
    st.download_button("엑셀로 다운로드", data=output, file_name='부동산_데이터.csv')

# 추가적인 사용자 인터페이스 개선 사항
st.sidebar.title("설정")
table_width = st.sidebar.slider("표 너비 조정", min_value=300, max_value=1000, value=600)

# 가상의 데이터프레임 표시
st.dataframe(data, width=table_width)
