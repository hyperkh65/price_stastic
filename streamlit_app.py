import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from datetime import datetime
import json
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
st.title("부동산 데이터 조회")

# 왼쪽 고정탭
st.sidebar.title("진행 현황")
si_do_name = st.sidebar.text_input("시/도를 입력하세요 (예: 서울특별시) 또는 '전국' 입력", "전국")
start_year_month = st.sidebar.text_input("조회 시작 년월 (YYYYMM 형식, 예: 202301)", "")
end_year_month = st.sidebar.text_input("조회 종료 년월 (YYYYMM 형식, 예: 202312)", "")

# 현재 날짜를 기준으로 기간 설정
now = datetime.now()
if not start_year_month:
    start_year_month = f"{now.year}01"
if not end_year_month:
    end_year_month = now.strftime("%Y%m")

# 진행 상태 변수
status_text = st.sidebar.empty()
progress_bar = st.sidebar.progress(0)

# 데이터를 조회하는 버튼을 추가하여, 사용자 입력 후에만 데이터 처리를 시작합니다.
if st.button("데이터 조회"):
    if si_do_name and start_year_month and end_year_month:
        # DistrictConverter 인스턴스 생성
        converter = DistrictConverter()

        # 데이터 수집 및 처리
        all_data = pd.DataFrame()

        if si_do_name == "전국":
            total_records = sum(len(converter.get_sigungu(district["si_do_code"])) for district in converter.districts)
            processed_records = 0
            
            for district in converter.districts:
                si_do_code = district["si_do_code"]
                sigungu_list = district["sigungu"]
                for sigungu in sigungu_list:
                    sigungu_code = sigungu["sigungu_code"]
                    sigungu_name = sigungu["sigungu_name"]

                    # 현재 처리 중인 지역을 업데이트
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
                    processed_records += 1
                    progress_bar.progress(processed_records / total_records)

        else:
            si_do_code = converter.get_si_do_code(si_do_name)
            sigungu_list = converter.get_sigungu(si_do_code)
            total_records = len(sigungu_list)
            processed_records = 0

            for sigungu in sigungu_list:
                sigungu_code = sigungu["sigungu_code"]
                sigungu_name = sigungu["sigungu_name"]

                # 현재 처리 중인 지역을 업데이트
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
                processed_records += 1
                progress_bar.progress(processed_records / total_records)

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

        # 데이터 다운로드 옵션 추가
        st.write("### 데이터 다운로드")
        excel_filename = f"{si_do_name}_{start_year_month}_{end_year_month}_매매.xlsx"
        csv_filename = f"{si_do_name}_{start_year_month}_{end_year_month}_매매.csv"

        # 엑셀 다운로드 (BytesIO로 메모리에 저장)
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            selected_data.to_excel(writer, index=False)
        output.seek(0)

        st.download_button(
            label="엑셀로 다운로드",
            data=output,
            file_name=excel_filename,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        # CSV 다운로드
        st.download_button(
            label="CSV로 다운로드",
            data=selected_data.to_csv(index=False),
            file_name=csv_filename,
            mime='text/csv'
        )
    else:
        st.error("모든 필드를 채워주세요.")
