import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# 지역 코드 변환기 클래스
class DistrictConverter:
    def __init__(self):
        self.districts = self.__read_district_file()

    def __read_district_file(self):
        with open('district.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_district_code(self, si_do_name):
        return self.districts.get(si_do_name, None)

# 데이터 로드 함수
def load_data(si_do_name, start_date, end_date):
    # 실제 데이터 로드 로직을 구현해야 함
    # 예시로 더미 데이터를 반환
    date_range = pd.date_range(start=start_date, end=end_date, freq='M')
    data = pd.DataFrame({
        'date': date_range,
        'district': ['District A', 'District B'] * (len(date_range) // 2),
        'transaction_amount': [30000000, 35000000] * (len(date_range) // 2),
        'area': [50, 60] * (len(date_range) // 2)
    })
    return data

# 시각화 함수들
def visualize_data(data):
    st.subheader("시각화 결과")

    # 히스토그램
    st.subheader("매매가 분포 히스토그램")
    plt.figure(figsize=(10, 5))
    sns.histplot(data['transaction_amount'], bins=10, kde=True)
    st.pyplot(plt)

    # 상자 수염 그림
    st.subheader("지역별 매매가 상자 수염 그림")
    plt.figure(figsize=(10, 5))
    sns.boxplot(x='district', y='transaction_amount', data=data)
    st.pyplot(plt)

    # 시간 시리즈 그래프
    st.subheader("시간에 따른 매매가 변화")
    monthly_avg = data.groupby(data['date'].dt.to_period('M')).mean()
    plt.figure(figsize=(10, 5))
    plt.plot(monthly_avg.index.astype(str), monthly_avg['transaction_amount'], marker='o')
    plt.xticks(rotation=45)
    st.pyplot(plt)

    # 산점도
    st.subheader("전용면적과 매매가의 관계")
    plt.figure(figsize=(10, 5))
    sns.scatterplot(x='area', y='transaction_amount', data=data)
    st.pyplot(plt)

# 인터페이스 설정
st.title("부동산 매매가 데이터 분석")
st.markdown("## 데이터 조회를 위해 아래 정보를 입력하세요.")

# 사용자 입력
si_do_name = st.text_input("시/도명 입력:", "서울특별시")
start_date = st.date_input("시작 날짜", value=datetime(2020, 1, 1))
end_date = st.date_input("종료 날짜", value=datetime(2021, 12, 31))

if st.button("데이터 조회"):
    district_converter = DistrictConverter()
    district_code = district_converter.get_district_code(si_do_name)

    if district_code is None:
        st.error("유효하지 않은 시/도명입니다.")
    else:
        data = load_data(si_do_name, start_date, end_date)
        st.dataframe(data)  # 표 먼저 표시
        visualize_data(data)  # 시각화 호출

# 진행률 및 상태 표시
st.sidebar.markdown("## 진행 상태")
st.sidebar.write(f"현재 검토 지역: {si_do_name}")
st.sidebar.write(f"진행율: {100 * (end_date - start_date).days / (datetime.now() - start_date).days:.2f}%")
st.sidebar.write("진행한 검사 수: 50")
st.sidebar.write("남은 검사 수: 10")
