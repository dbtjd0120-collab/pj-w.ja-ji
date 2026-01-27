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

        self.code_to_name = {
        s["역사코드"]: s["역사명"]
        for s in self.stations_raw
        }

        self.name_line_to_code = {}
        for s in self.stations_raw:
            self.name_line_to_code[(s["역사명"], s["호선"])] = s["역사코드"]

    
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

    def _build_indices(self):
        self.code_to_name = {
        s["역사코드"]: s["역사명"]
        for s in self.stations_raw
    }
        

    def _time_to_seconds(self, time_str=None):
        """
        HH:MM:SS 또는 MM:SS 형식의 시간을 초(int)로 변환한다.

        - time_str이 None이면 현재 시간을 기준으로 초를 반환한다.
        - HH:MM:SS → 시*3600 + 분*60 + 초
        - MM:SS    → 분*60 + 초

        예시:
            time_to_seconds("01:02:03") -> 3723
            time_to_seconds("12:34")    -> 754
            time_to_seconds()           -> 현재 시각 기준 초
        """

        if time_str is None:
            now = datetime.now()
            return now.hour * 3600 + now.minute * 60 + now.second

        parts = time_str.split(":")

        try:
            if len(parts) == 3:
                hour, minute, second = map(int, parts)
            elif len(parts) == 2:
                hour = 0
                minute, second = map(int, parts)
            else:
                raise ValueError

            if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
                raise ValueError

        except ValueError:
            raise ValueError("시간 형식은 'HH:MM:SS' 또는 'MM:SS' 이어야 합니다.")

        return hour * 3600 + minute * 60 + second
    
    def _sec_to_hhmm(self, sec):
        sec = int(sec)
        h = sec // 3600
        m = (sec % 3600) // 60
        return f"{h:02d}:{m:02d}"

    
    def get_user_input(self):
        """
        사용자로부터 출발역, 도착역, 출발 시간, 경로 기준을 입력받는다.
        시간 형식:
        - HH:MM:SS
        - MM:SS
        - 엔터 입력 시 현재 시간 사용
        경로 기준:
        - 0: 최단시간
        - 1: 최소환승
        반환:
        (start_station, end_station, start_time_sec, mode)
        """

        # --------------------
        # 역 이름 목록 (존재 검증용)
        # --------------------
        station_names = {station["역사명"] for station in self.stations_raw}

        # --------------------
        # 출발역 / 도착역 입력
        # --------------------
        while True:
            start = input("출발역을 입력하세요: ").strip()
            end = input("도착역을 입력하세요: ").strip()

            if not start or not end:
                print("❌ 역 이름은 비어 있을 수 없습니다.")
                continue

            if start not in station_names:
                print(f"❌ 존재하지 않는 역입니다: {start}")
                continue

            if end not in station_names:
                print(f"❌ 존재하지 않는 역입니다: {end}")
                continue

            if start == end:
                print("❌ 출발역과 도착역은 같을 수 없습니다.")
                continue

            break

        # --------------------
        # 출발 시간 입력
        # --------------------
        while True:
            time_input = input(
                "출발 시간을 입력하세요 (HH:MM:SS 또는 MM:SS, 엔터 시 현재 시간): "
            ).strip()

            if time_input == "":
                start_time_sec = self._time_to_seconds(None)
                break

            start_time_sec = self._time_to_seconds(time_input)
            if start_time_sec is None:
                print("❌ 시간 형식이 올바르지 않습니다.")
                continue

            break

        # --------------------
        # 경로 기준 선택
        # --------------------
        while True:
            mode_input = input(
                "경로 기준을 선택하세요 (0=최단시간, 1=최소환승): "
            ).strip()

            if mode_input in ("0", "1"):
                mode = int(mode_input)
                break

            print("❌ 0 또는 1만 입력하세요.")

        return start, end, start_time_sec, mode

    def find_best_path(self, start, end, start_time_sec, mode):


        print("===== 환승 JSON 전체 구조 =====")
        print("총 환승역 개수:", len(self.transfers))
        for k, v in list(self.transfers.items())[:5]:  # 앞 5개만
            print(f"역코드 {k} -> {v}")
        print("================================")
            
        """
        mode = 0 : 최단시간
        mode = 1 : 최소환승
        """

        import heapq
        INF = float("inf")

        # -------------------------------------------------
        # 상태 정의
        # state = (node, line)
        # best_time[state] = 해당 상태의 최소 도착 시간 (float)
        # -------------------------------------------------
        best_time = {}
        prev = {}

        pq = []

        end_nodes = {
            station["역사코드"]
            for station in self.stations_raw
            if station["역사명"] == end
        }


        # -------------------------------------------------
        # 1️⃣ 출발역 초기화
        # 같은 역이라도 호선별로 다른 상태
        # -------------------------------------------------
        for station in self.stations_raw:
            if station["역사명"] == start:
                node = station["역사코드"]
                line = station["호선"]

                state = (node, line)
                best_time[state] = (start_time_sec, 0)  # (시간, 환승)

                if mode == 0:
                    # (시간, 환승, node, line)
                    heapq.heappush(pq, (start_time_sec, 0, node, line))
                else:
                    # (환승, 시간, node, line)
                    heapq.heappush(pq, (0, start_time_sec, node, line))

        # -------------------------------------------------
        # 2️⃣ 다익스트라 탐색
        # -------------------------------------------------
        while pq:
            if mode == 0:
                cur_time, cur_transfer, cur_node, cur_line = heapq.heappop(pq)
            else:
                cur_transfer, cur_time, cur_node, cur_line = heapq.heappop(pq)

            state = (cur_node, cur_line)

            print(f"[POP] node={cur_node}, time={cur_time}, transfer={cur_transfer}")

            print("cur_node =", cur_node, "cur_line =", cur_line)
            print("transfer at node =", self.transfers.get(cur_node))
            print("end_nodes =", end_nodes)


            # -------------------------------------------------
            # 🔥 가지치기
            # 이미 더 빠른 도착 기록이 있으면 스킵
            # -------------------------------------------------
            best_t, best_tr = best_time.get(state, (INF, INF))
            if mode == 0:

                if cur_time > best_t:
                    continue
            else:
                    
                if (cur_transfer, cur_time) > (best_tr, best_t):
                    continue
                if cur_transfer == best_tr and cur_time > best_t:
                    continue

            # -------------------------------------------------
            # 3️⃣ 도착 판정 (역명 기준)
            # -------------------------------------------------
            if cur_node in end_nodes:
                return {
                    "end_state": state,
                    "arrive_time": cur_time,
                    "transfer_count": cur_transfer,
                    "prev": prev
                }

            # -------------------------------------------------
            # 4️⃣ 열차 이동 (같은 호선만)
            # -------------------------------------------------
            for edge in self.graph.get(cur_node, []):

                # 다른 호선 불가
                if edge["line"] != cur_line:
                    continue

                # 이미 출발한 열차는 탈 수 없음
                if edge["dept_time"] < cur_time:
                    continue

                next_node = edge["dest_code"]
                next_line = cur_line
                next_time = edge["arr_time"]
                next_transfer = cur_transfer

                next_state = (next_node, next_line)

                # 🔥 시간 또는 환승으로 가지치기
                best_t, best_tr = best_time.get(next_state, (INF, INF))

                if mode == 0:
                    # 최단시간
                    if next_time >= best_t:
                        continue
                else:
                    # 최소환승
                    if (next_transfer, next_time) >= (best_tr, best_t):
                        continue
                
                
                best_time[next_state] = (next_time, next_transfer)

                prev[next_state] = {
                    "prev": state,
                    "type": "train",
                    "train_code": edge["train_code"],
                    "dept_time": edge["dept_time"],
                    "arr_time": edge["arr_time"]
                }

                if mode == 0:
                    heapq.heappush(
                        pq, (next_time, next_transfer, next_node, next_line)
                    )
                else:
                    heapq.heappush(
                        pq, (next_transfer, next_time, next_node, next_line)
                    )

            # -------------------------------------------------
            # 5️⃣ 환승 이동 (transfer_list 기반)
            # -------------------------------------------------
            if cur_node in self.transfers:
                for key, info in self.transfers[cur_node].items():
                    from_line, to_line = key.split(":")

                    if from_line != cur_line:
                        continue
                    
                    station_name = self.code_to_name[cur_node]
                    next_node = self.name_line_to_code[(station_name, to_line)]
                    next_line = to_line
                    next_time = cur_time + info["walk_sec"]
                    next_transfer = cur_transfer + 1

                    next_state = (next_node, next_line)

                    # 🔥 환승도 "시간" 기준으로만 컷
                    best_t, best_tr = best_time.get(next_state, (INF, INF))

                    if mode == 0:
                        if next_time >= best_t:
                            continue
                    else:
                        if (next_transfer, next_time) >= (best_tr, best_t):
                            continue
                    best_time[next_state] = (next_time, next_transfer)

                    prev[next_state] = {
                        "prev": state,
                        "type": "transfer",
                        "walk_sec": info["walk_sec"]
                    }

                    if mode == 0:
                        heapq.heappush(
                            pq, (next_time, next_transfer, next_node, next_line)
                        )
                    else:
                        heapq.heappush(
                            pq, (next_transfer, next_time, next_node, next_line)
                        )

        # -------------------------------------------------
        # ❌ 경로 없음
        # -------------------------------------------------
        return None

    

    def reconstruct_path(self, end_state, prev):
        path = []
        cur = end_state

        while cur in prev:
            info = prev[cur]
            path.append((cur, info))
            cur = info["prev"]

        # 출발 노드
        path.append((cur, None))

        return list(reversed(path))


        


if __name__ == "__main__":
    pathfinder = SubwayPathfinder()

    # 사용자 입력
    start, end, start_time_sec, mode = pathfinder.get_user_input()

    print("\n===== 입력값 =====")
    print(f"출발역: {start}")
    print(f"도착역: {end}")
    print(f"출발시간(초): {start_time_sec}")
    print(f"모드: {'최단시간' if mode == 0 else '최소환승'}")

    
    result = pathfinder.find_best_path(
        start,
        end,
        start_time_sec,
        mode
    )

    print("\n===== 탐색 결과 =====")
    if result is None:
        print("❌ 경로를 찾지 못했습니다.")
        exit()
    else:
        print(f"도착시간: {pathfinder._sec_to_hhmm(result['arrive_time'])}")
        print(
                f"총 소요 시간: "
            f"{int((result['arrive_time'] - start_time_sec) // 60)}분"
        )
        print(f"환승 횟수: {result['transfer_count']}")

result = pathfinder.find_best_path(start, end, start_time_sec, mode)

path = pathfinder.reconstruct_path(
    result["end_state"],
    result["prev"]
)

for state, info in path:
    node, line = state

    if info is None:
        print(
            f"출발: {pathfinder.code_to_name[node]} ({line}호선) "
            f"{pathfinder._sec_to_hhmm(start_time_sec)}"
        )

        continue

    if info["type"] == "train":
        print(
            f"{pathfinder.code_to_name[node]} ({line}호선) ← "
            f"[열차 {info['train_code']}] "
            f"{pathfinder._sec_to_hhmm(info['dept_time'])} → "
            f"{pathfinder._sec_to_hhmm(info['arr_time'])}"
        )

    else:
        print(
            f"{pathfinder.code_to_name[node]} ({line}호선) ← "
            f"[환승 {info['walk_sec']}초]"
        )



