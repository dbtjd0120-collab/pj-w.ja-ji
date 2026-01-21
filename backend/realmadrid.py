import os
import json
import heapq
from datetime import datetime

# --- 경로 설정 ---
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(current_file)
project_root = os.path.dirname(backend_dir)
DATA_DIR = os.path.join(project_root, 'data', 'processed')

class SubwayPathfinder:
    def __init__(self):
        """
        함수 정의 앞에 붙은 _ 두개는 name mangling(이름변경). 규칙에 따라 외부에서 접근 불가
        같은 클래스의 다른 함수를 사용할 것이라 self를 인자로 정의함
        """
        self.day_type = self._get_today_type()
        self._load_data()
        self._build_indices()
        # print(f"[{self.day_type}] 데이터 로딩 완료. 탐색 준비가 되었습니다.")

    def _get_today_type(self):
        """
        오늘 요일을 기준으로 시간표 타입을 반환한다.
        weekday / saturday / holiday
        """
        weekday = datetime.now().weekday()  # 월=0, ..., 일=6

        if weekday < 5:
            return 'weekday'
        elif weekday == 5:
            return 'saturday'
        else:
            return 'holiday'


    def _load_data(self):
        try:
            # --- 요일별 운행 그래프 파일 선택 ---
            if self.day_type == 'weekday':
                graph_file = 'graph_weekday.json'
            elif self.day_type == 'saturday':
                graph_file = 'graph_saturday.json'
            else:  # holiday
                graph_file = 'graph_holiday.json'

            # --- 열차 운행 그래프 로드 ---
            with open(os.path.join(DATA_DIR, graph_file), 'r', encoding='EUC-KR') as f:
                self.graph = json.load(f)

            # --- 환승 정보 로드 ---
            with open(os.path.join(DATA_DIR, 'transfer_list.json'), 'r', encoding='EUC-KR') as f:
                self.transfers = json.load(f)

            # --- 역 메타 정보 로드 ---
            with open(os.path.join(DATA_DIR, 'stations_list.json'), 'r', encoding='EUC-KR') as f:
                self.stations_raw = json.load(f)

        except Exception as e:
            print(f"❌ 데이터 로딩 실패: {e}")
            exit()







from datetime import datetime, timedelta


def get_user_input():
    start_station = input("출발역을 입력하세요: ").strip()
    end_station = input("도착역을 입력하세요: ").strip()

    time_input = input(
        "출발 시각을 입력하세요 (HH:MM, 엔터 시 현재 시각): "
    ).strip()

    if time_input == "":
        start_time = datetime.now()
    else:
        try:
            now = datetime.now()
            hour, minute = map(int, time_input.split(":"))
            start_time = now.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0
            )

            # ⚠️ 입력 시간이 이미 지난 경우 → 다음 날로 해석
            if start_time < now:
                start_time += timedelta(days=1)

        except Exception:
            raise ValueError("시간 형식이 올바르지 않습니다. HH:MM 형식으로 입력하세요.")

    return start_station, end_station, start_time
