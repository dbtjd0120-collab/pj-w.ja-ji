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

    def _get_today_type(self):  # 날짜를 요일로   + 한국의 현재 시간을 불러오는 datetime.now().time()도 고려 해볼만함.
        """함수 정의 앞에 붙은 _ 하나는 내부용(private) 메서드임을 나타냄"""
        def _get_today_type(self):
            day_type = datetime.now().weekday() #오늘이 무슨 요일인지 월:0 - 일:6으로 표현
            if day_type < 5: return 'weekday'
            elif day_type == 5: return 'saturday'
            else: return 'holiday'

    def _load_data(self):       # 데이터 로드
        try:
            with open(os.path.join(DATA_DIR, f'graph_{self.day_type}.json'), 'r', encoding='EUC-KR') as f:
                self.graph = json.load(f)   # 각각의 요일 별 json 파일이 없으므로 if self.day_type >= 5:
                                                                         #    graph_file = "graph_weekend.json"
                                                                            #       else:
                                                                             #  graph_file = "graph_weekday.json" 매핑 필요
            with open(os.path.join(DATA_DIR, 'transfer_list.json'), 'r', encoding='EUC-KR') as f:
                self.transfers = json.load(f)
            with open(os.path.join(DATA_DIR, 'stations_list.json'), 'r', encoding='EUC-KR') as f:
                self.stations_raw = json.load(f)
        except Exception as e:
            print(f"❌ 로딩 실패: {e}")
            exit()

    def _build_indices(self):
        self.name_to_codes = {}
        self.code_to_info = {}
        self.station_group = {}
        for st in self.stations_raw:
            code, name, line = st['역사코드'], st['역사명'], st['호선']
            self.code_to_info[code] = st  #단일 역 코드
            self.name_to_codes.setdefault(name, []).append(code) # 역 이름에 대해 여려 역사 코드 저장 
            self.station_group.setdefault(name, {})[line] = code # 환승 위해 환승 가능 역에 대한 다른 호선 역 코드 저장

    def search(self, start_name, end_name, departure_time_str):  # <------  def search(self, start_name, end_name, departure_time=None):
        """최단 시간과 최소 환승 두 가지 경로를 모두 반환"""                      #     if departure_time is None:
        print(f"\n🔍 '{start_name}' -> '{end_name}' 경로 탐색 중...")        #      departure_time = datetime.now(ZoneInfo("Asia/Seoul"))
                                                                            # 으로 시간 입력 시에는 지정 시간으로, 입력 ㄴㄴ시 현재 시간으로 부터 출발. 
        # 1. 최단 시간 경로 (급행 자동 고려)
        fastest = self.find_path(start_name, end_name, departure_time_str, mode='fastest')
        
        # 2. 최소 환승 경로
        min_transfer = self.find_path(start_name, end_name, departure_time_str, mode='min_transfer')
        
        self._display_results(fastest, min_transfer)

    def find_path(self, start_name, end_name, departure_time_str, mode='fastest'):
        start_codes = self.name_to_codes.get(start_name)
        end_codes = self.name_to_codes.get(end_name)
        if not start_codes or not end_codes: return None

        start_time = TimeUtils.str_to_seconds(departure_time_str) # 이름은 나오는데 정의는 안 보이는 유틸리티 클래스?????????????
        pq = [] # (비용, 현재시간, 현재코드, 환승횟수, 경로로그)            # 시간 문자열 ↔ 초 단위 정수 변환을 담당하는 사용자 정의 유틸리티 클래스(또는 모듈)
        min_costs = {}                                                 # 클래스 또는 모듈 정의 필요.

        for code in start_codes:
            info = self.code_to_info[code]
            heapq.heappush(pq, (start_time, start_time, code, 0, [{
                "station": start_name, "line": info['호선'], "time": TimeUtils.seconds_to_str(start_time), "type": "START"
            }]))                                                    #*********#          
                    #최종적으로 pq안에 (30600, 30600, "0150", 0, [...]) 와 (30600, 30600, "4251", 0, [...]) 둘 다 들어있음. 다익스트라 알아서 함.


        while pq:
            cost, curr_time, curr_code, transfer_count, path = heapq.heappop(pq)

            if curr_code in min_costs and min_costs[curr_code] <= cost: continue
            min_costs[curr_code] = cost  # 위 조건에 부합하면 continue 바로 오는 코드 무시.

            if curr_code in end_codes:
                return {"path": path, "duration": curr_time - start_time, "transfers": transfer_count}

            # --- [열차 이동] ---
            schedule = self.graph.get(curr_code, [])   #현재 역에서 출발 가능한 모든 열차/이동 스케줄을 가져와라
            idx = self._get_start_index(schedule, curr_time)
            # 다시 보기
            if idx != -1:
                visited_dests = set()
                # 급행/일반 열차를 모두 고려하기 위해 주변 시간대 탐색
                for i in range(idx, min(idx + 30, len(schedule))): # 탈 수 있는 열차 중에 30만큼만 내다보자
                    train = schedule[i]
                    dest_code = train['dest_code']
                    
                    # 같은 목적지라면 더 빨리 도착하는 열차(주로 급행)가 먼저 큐에서 처리됨
                    if dest_code in visited_dests: continue  # 늦게 타더라도 환승해서 급행 타는 경우, 취약. 
                    visited_dests.add(dest_code)             #도착역이 중복되면 가장 빠른 열차만 고려, 
                                                             #도착역 비교가 아닌 정차역 비교를 통해서 급행 중에서 가장 빠른 열차도 선택 할 수 있게 한다면?
                    # 가중치 계산: 최단시간 모드일 땐 실제 도착시간이 곧 비용
                    # 최소환승 모드일 땐 시간보다 환승 횟수가 중요하므로 아래 환승 파트에서 페널티 부여
                    new_cost = train['arr_time']
                    
                    new_path = path + [{
                        "station": train['dest_name'], "line": train['line'], 
                        "time": TimeUtils.seconds_to_str(train['arr_time']), "type": "MOVE",
                        "express": "급행" in train.get('train_code', '')
                    }]
                    heapq.heappush(pq, (new_cost, train['arr_time'], dest_code, transfer_count, new_path))

            # --- [환승 이동] ---
            if curr_code in self.transfers:
                for key, val in self.transfers[curr_code].items():# 현재 역에서 환승 가능 역이 있다며 그 모든 경우를 다익스라 후보로 추가
                    target_line = key.split(':')[1]
                    target_code = self.station_group[self.code_to_info[curr_code]['역사명']].get(target_line)
                    
                    if target_code:
                        arrival_time = curr_time + val['walk_sec']
                        new_transfers = transfer_count + 1
                        
                        # 최소 환승 모드일 경우 환승 1회당 30분의 시간 페널티를 부여하여 경로 우회 유도
                        cost_penalty = arrival_time + (1800 * new_transfers if mode == 'min_transfer' else 0)
                        
                        new_path = path + [{
                            "station": self.code_to_info[curr_code]['역사명'], "line": target_line,
                            "time": TimeUtils.seconds_to_str(arrival_time), "type": "TRANSFER"
                        }]
                        heapq.heappush(pq, (cost_penalty, arrival_time, target_code, new_transfers, new_path))
        return None

    def _get_start_index(self, schedule, current_time):### 스케쥴 딕셔너리 {} 는 같은 역을 지나는 같은 호선의 시간값으로 정렬. 
        low, high = 0, len(schedule) - 1     # 143 번째 <=으로 len(스케줄)-1 배열 인덱스는 0부터 시작
        res = -1                                
        while low <= high:
            mid = (low + high) // 2  # 딕셔너리를 반으로 나누어서 
            if schedule[mid]['dept_time'] >= current_time: #반으로 나눈 mid 번째와 비교
                res = mid       
                high = mid - 1  #1st high = 4 - 1, mid =2,res = 2, low = 0, 2nd  mid = 0, low = 1, high =1 3rd mid =1, low = 2 4번쨰 없음(low>high)
            else: low = mid + 1
        return res   # 따라서, 스케줄의 두번째 열차를 타는 것이 제일 빠르다.

    def _display_results(self, fastest, min_trans):
        def print_p(data, title):
            print(f"\n[ {title} ]")
            if not data: 
                print("경로를 찾을 수 없습니다.")
                return
            print(f"⏱ 소요시간: {data['duration']//60}분 | 🔄 환승: {data['transfers']}회")
            for s in data['path']:
                if s['type'] == 'START': print(f"({s['time']}) {s['station']} [{s['line']}] 출발")
                elif s['type'] == 'MOVE': 
                    exp_tag = "[급행]" if s.get('express') else ""
                    print(f"  ↓ {exp_tag} {s['station']} 도착 ({s['time']})")
                elif s['type'] == 'TRANSFER': print(f"  ━━ {s['station']}역 {s['line']}으로 환승 ━━")

        print_p(fastest, "⚡ 최단 시간 경로")
        # 최단시간과 최소환승이 같은 경로면 생략
        if min_trans and fastest and min_trans['path'] != fastest['path']:
            print_p(min_trans, "🔄 최소 환승 경로")
        elif min_trans:
            print("\n💡 최소 환승 경로가 최단 시간 경로와 동일합니다.")

# --- 실행부 ---
if __name__ == "__main__":
    pathfinder = SubwayPathfinder()
    s = input("출발역 입력 (예: 상수): ").strip()
    e = input("도착역 입력 (예: 공릉): ").strip()
    t = input("현재 시각 (HH:MM): ").strip()
    pathfinder.search(s, e, t)