import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from PublicDataReader import TransactionPrice
from datetime import datetime

# PublicDataReader API 서비스 키 (환경 변수로 설정된 키를 불러옵니다)
service_key = st.secrets["SERVICE_KEY"]
api = pdr.TransactionPrice(service_key)

class DistrictConverter:
    def __init__(self):
        self.districts = self.__read_district_file()

    def __read_district_file(self):
        # JSON 파일 경로 (환경 변수로 지정한 파일 경로 사용)
        json_file_path = st.secrets["DISTRICT_JSON_PATH"]
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

# Streamlit 앱 구성
def main():
    st.title("부동산 데이터 조회")

    si_do_name = st.text_input("시/도를 입력하세요 (예: 서울특별시)", "서울특별시")
    start_year_month = st.text_input("조회 시작 년월 (YYYYMM 형식, 예: 202301)", "202301")
    end_year_month = st.text_input("조회 종료 년월 (YYYYMM 형식, 예: 202312)", "202312")

    # DistrictConverter 인스턴스 생성
    converter = DistrictConverter()

    si_do_code = converter.get_si_do_code(si_do_name)
    sigungu_list = converter.get_sigungu(si_do_code)

    # 모든 시/군/구 데이터를 수집할 DataFrame 초기화
    all_data = pd.DataFrame()

    for sigungu in sigungu_list:
        sigungu_code = sigungu["sigungu_code"]
        sigungu_name = sigungu["sigungu_name"]

        st.write(f"{sigungu_name} 데이터를 처리 중입니다...")

        # 부동산 데이터를 가져옴
        df = api.get_data(
            property_type="아파트",
            trade_type="매매",
            sigungu_code=sigungu_code,
            start_year_month=start_year_month,
            end_year_month=end_year_month
        )

        # 시/군/구 이름 및 시/도 이름을 새로운 컬럼으로 추가
        df["sigungu_name"] = sigungu_name
        df["si_do_name"] = si_do_name

        # 가져온 데이터를 all_data에 추가
        all_data = pd.concat([all_data, df], ignore_index=True)

    # 데이터 열 이름을 한국어로 변환
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

    # 필요한 열만 남기고 한국어 열 이름으로 변경
    selected_data = all_data.rename(columns=columns_to_select)[list(columns_to_select.values())]

    # 데이터를 표로 표시
    st.write("조회 결과")
    st.dataframe(selected_data)

    # 데이터 다운로드 옵션 추가
    st.download_button(
        label="엑셀로 다운로드",
        data=selected_data.to_excel(index=False),
        file_name="real_estate_data.xlsx"
    )

    st.download_button(
        label="CSV로 다운로드",
        data=selected_data.to_csv(index=False),
        file_name="real_estate_data.csv"
    )

if __name__ == "__main__":
    main()
