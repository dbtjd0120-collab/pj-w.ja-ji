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

    def _get_today_type(self):  # 날짜를 요일로
        """함수 정의 앞에 붙은 _ 하나는 내부용(private) 메서드임을 나타냄"""
        def _get_today_type(self):
            day_type = datetime.now().weekday()
            if day_type < 5: return 'weekday'
            elif day_type == 5: return 'saturday'
            else: return 'holiday'

    def _load_data(self):       # 데이터 로드
        try:
            with open(os.path.join(DATA_DIR, f'graph_{self.day_type}.json'), 'r', encoding='EUC-KR') as f:
                self.graph = json.load(f)
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
            self.code_to_info[code] = st
            self.name_to_codes.setdefault(name, []).append(code)
            self.station_group.setdefault(name, {})[line] = code

    def search(self, start_name, end_name, departure_time_str):
        """최단 시간과 최소 환승 두 가지 경로를 모두 반환"""
        print(f"\n🔍 '{start_name}' -> '{end_name}' 경로 탐색 중...")
        
        # 1. 최단 시간 경로 (급행 자동 고려)
        fastest = self.find_path(start_name, end_name, departure_time_str, mode='fastest')
        
        # 2. 최소 환승 경로
        min_transfer = self.find_path(start_name, end_name, departure_time_str, mode='min_transfer')
        
        self._display_results(fastest, min_transfer)

    def find_path(self, start_name, end_name, departure_time_str, mode='fastest'):
        start_codes = self.name_to_codes.get(start_name)
        end_codes = self.name_to_codes.get(end_name)
        if not start_codes or not end_codes: return None

        start_time = self._str_to_seconds(departure_time_str)
        pq = [] # (비용, 현재시간, 현재코드, 환승횟수, 경로로그)
        min_costs = {}

        for code in start_codes:
            info = self.code_to_info[code]
            heapq.heappush(pq, (start_time, start_time, code, 0, [{
                "station": start_name, "line": info['호선'], "time": self._seconds_to_str(start_time), "type": "START"
            }]))

        while pq:
            cost, curr_time, curr_code, transfer_count, path = heapq.heappop(pq)

            if curr_code in min_costs and min_costs[curr_code] <= cost: continue
            min_costs[curr_code] = cost

            if curr_code in end_codes:
                return {"path": path, "duration": curr_time - start_time, "transfers": transfer_count}

            # --- [열차 이동] ---
            schedule = self.graph.get(curr_code, [])
            idx = self._get_start_index(schedule, curr_time)
            
            if idx != -1:
                visited_dests = set()
                # 급행/일반 열차를 모두 고려하기 위해 주변 시간대 탐색
                for i in range(idx, min(idx + 30, len(schedule))):
                    train = schedule[i]
                    dest_code = train['dest_code']
                    
                    # 같은 목적지라면 더 빨리 도착하는 열차(주로 급행)가 먼저 큐에서 처리됨
                    if dest_code in visited_dests: continue
                    visited_dests.add(dest_code)

                    # 가중치 계산: 최단시간 모드일 땐 실제 도착시간이 곧 비용
                    # 최소환승 모드일 땐 시간보다 환승 횟수가 중요하므로 아래 환승 파트에서 페널티 부여
                    new_cost = train['arr_time']
                    
                    new_path = path + [{
                        "station": train['dest_name'], "line": train['line'], 
                        "time": self._seconds_to_str(train['arr_time']), "type": "MOVE",
                        "express": "급행" in train.get('train_code', '')
                    }]
                    heapq.heappush(pq, (new_cost, train['arr_time'], dest_code, transfer_count, new_path))

            # --- [환승 이동] ---
            if curr_code in self.transfers:
                for key, val in self.transfers[curr_code].items():
                    target_line = key.split(':')[1]
                    target_code = self.station_group[self.code_to_info[curr_code]['역사명']].get(target_line)
                    
                    if target_code:
                        arrival_time = curr_time + val['walk_sec']
                        new_transfers = transfer_count + 1
                        
                        # 최소 환승 모드일 경우 환승 1회당 30분의 시간 페널티를 부여하여 경로 우회 유도
                        cost_penalty = arrival_time + (1800 * new_transfers if mode == 'min_transfer' else 0)
                        
                        new_path = path + [{
                            "station": self.code_to_info[curr_code]['역사명'], "line": target_line,
                            "time": self._seconds_to_str(arrival_time), "type": "TRANSFER"
                        }]
                        heapq.heappush(pq, (cost_penalty, arrival_time, target_code, new_transfers, new_path))
        return None
    
    def _str_to_seconds(t_str):
        """ 문자열(HH:MM:SS) -> 초(int) 변환 """
        if t_str is None or t_str != t_str:  # t_str != t_str 은 NaN을 체크하는 방법
            return None

        try:
            parts = list(map(int, str(t_str).split(':')))       # HH:MM:SS 또는 MM:SS 형태로 정수 list 생성 (길이는 알아서)
            if len(parts) == 3: return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2: return parts[0] * 60 + parts[1]
            return 0
        except:
            return 0
        
    def _seconds_to_str(seconds):
        """ 초(int) -> 문자열(HH:MM:SS) 변환 """
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02}"

    def _get_start_index(self, schedule, current_time):
        low, high = 0, len(schedule) - 1
        res = -1
        while low <= high:
            mid = (low + high) // 2
            if schedule[mid]['dept_time'] >= current_time:
                res = mid
                high = mid - 1
            else: low = mid + 1
        return res

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