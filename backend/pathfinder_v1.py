import os
import json
import heapq
import time

# --- 경로 설정 ---
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(current_file)
project_root = os.path.dirname(backend_dir)
DATA_DIR = os.path.join(project_root, 'data', 'processed')
 
class SubwayPathfinder:
    def __init__(self, day_type='weekday'):
        print(f"[{day_type}] 데이터 로딩 중...")
        self.day_type = day_type
        
        # 1. 그래프 데이터 로드 (graph_weekday.json 등)
        graph_path = os.path.join(DATA_DIR, f'graph_{day_type}.json')
        with open(graph_path, 'r', encoding='EUC-KR') as f: # 전처리때 EUC-KR로 저장함
            self.graph = json.load(f)
            
        # 2. 환승 정보 로드
        with open(os.path.join(DATA_DIR, 'transfer_list.json'), 'r', encoding='EUC-KR') as f:
            self.transfers = json.load(f)
            
        # 3. 역 정보 로드 & 검색 인덱스 생성
        with open(os.path.join(DATA_DIR, 'stations_list.json'), 'r', encoding='EUC-KR') as f:
            self.stations = json.load(f)
        
        # 4. 역 이름으로 코드 찾기 & 같은 역끼리 묶기 (환승 연결용)
        # 구조: {'서울역': {'1': '0150', '4': '0426', ...}}
        self.station_name_map = {} 
        self.station_group = {}
        
        for st in self.stations:
            code = st['역사코드']
            name = st['역사명']
            line = st['호선']
            
            # 이름으로 코드 찾기 (검색용)
            if name not in self.station_name_map:
                self.station_name_map[name] = []
            self.station_name_map[name].append(code)
            
            # 환승 연결을 위해 같은 이름의 역들을 호선별로 그룹화
            if name not in self.station_group:
                self.station_group[name] = {}
            self.station_group[name][line] = code

    def _str_to_seconds(self, time_str):
        h, m = map(int, time_str.split(':'))
        return h * 3600 + m * 60

    def _seconds_to_str(self, seconds):
        return f"{seconds // 3600:02}:{(seconds % 3600) // 60:02}:{(seconds % 60):02}"

    def find_next_train(self, station_code, current_time):
        """
        이진 탐색(Binary Search)을 사용하여 
        현재 시간 이후에 출발하는 가장 빠른 열차를 찾음
        """
        if station_code not in self.graph:
            return None
            
        schedule = self.graph[station_code]
        
        # 스케줄이 비어있으면 운행 없음
        if not schedule:
            return None

        # 이진 탐색 직접 구현 (데이터가 딕셔너리 리스트라 bisect 모듈 바로 쓰기 애매함)
        left, right = 0, len(schedule) - 1
        idx = -1
        
        while left <= right:
            mid = (left + right) // 2
            if schedule[mid]['dept_time'] >= current_time:
                idx = mid
                right = mid - 1
            else:
                left = mid + 1
                
        if idx != -1:
            return schedule[idx]
        return None

    def find_path(self, start_name, end_name, departure_time_str):
        """최단 시간 경로 탐색 메인 함수"""
        
        # 1. 입력값 검증 및 초기화
        start_codes = self.station_name_map.get(start_name)
        end_codes = self.station_name_map.get(end_name)
        
        if not start_codes or not end_codes:
            return {"error": "존재하지 않는 역입니다."}

        start_time = self._str_to_seconds(departure_time_str)
        
        # 우선순위 큐: (누적시간(도착시간), 현재역코드, 경로로그)
        # 경로로그: [{"name":..., "action": "RIDE"|"WALK", ...}]
        pq = []
        
        # 최단 시간 기록용 (무한대로 초기화)
        min_times = {} 
        
        # 시작점이 환승역일 수 있으므로(예: 서울역 1호선, 4호선) 모든 가능성 큐에 넣기
        for code in start_codes:
            # 시작점의 호선 정보 가져오기
            line = self.station_group[start_name].get(str(code), "?") # 역코드로 호선 역추적은 생략하고 일단 진행
            # 역 정보에서 호선 찾기
            for st in self.stations:
                if st['역사코드'] == code:
                    line = st['호선']
                    break
            
            heapq.heappush(pq, (start_time, code, [{
                "station": start_name,
                "code": code,
                "line": line,
                "time": self._seconds_to_str(start_time),
                "type": "START"
            }]))
            min_times[code] = start_time

        # 2. 다익스트라 알고리즘 시작
        while pq:
            current_time, current_code, path_history = heapq.heappop(pq)
            
            # 이미 더 빠른 시간으로 방문한 적 있으면 스킵
            if current_code in min_times and min_times[current_code] < current_time:
                continue
            
            # 현재 역 정보 (이름, 호선) 찾기
            current_info = next((item for item in self.stations if item['역사코드'] == current_code), None)
            current_name = current_info['역사명']
            current_line = current_info['호선']

            # --- [목표 도착 확인] ---
            if current_code in end_codes:
                total_duration = current_time - start_time
                return {
                    "status": "success",
                    "path": path_history,
                    "departure_time": departure_time_str,
                    "arrival_time": self._seconds_to_str(current_time),
                    "duration_min": total_duration // 60,
                    "duration_sec": total_duration % 60
                }

            # --- [행동 1: 열차 탑승] ---
            # 현재 역에서 탈 수 있는 가장 빠른 열차 찾기
            # (같은 역에서 출발하는 열차들)
            
            # 주의: 여기서는 '모든' 열차를 다 보는게 아니라 이진탐색으로 바로 다음 열차 하나만 봅니다.
            # 하지만 1호선 구로역처럼 행선지가 갈라지는 경우(인천행/신창행)를 고려해야 하므로
            # 사실은 현재 시간 이후의 '모든 종류의 행선지'를 봐야 하지만, 
            # 단순화를 위해 graph에 저장된 '시간순 정렬' 데이터를 순차적으로 탐색하며
            # "가능한 모든 다음 역"을 큐에 넣습니다.
            
            # 성능 최적화: 현재 시간 이후의 열차들을 보되, 너무 먼 미래(예: 1시간 뒤)는 볼 필요 없음
            # 일단 단순하게 구현: graph 구조상 같은 역 출발이면 목적지가 달라도 리스트에 섞여 있음
            
            schedule_list = self.graph.get(current_code, [])
            # 이진 탐색으로 시작 인덱스 찾기
            left, right = 0, len(schedule_list) - 1
            start_idx = -1
            while left <= right:
                mid = (left + right) // 2
                if schedule_list[mid]['dept_time'] >= current_time:
                    start_idx = mid
                    right = mid - 1
                else:
                    left = mid + 1
            
            if start_idx != -1:
                # 현재 시간 이후 열차들을 확인
                # 같은 목적지로 가는 열차가 여러 대 있을 수 있는데, 그 중 가장 빠른 것만 타면 됨
                # 하지만 목적지가 다른 열차(A행, B행)는 각각 타봐야 함.
                visited_destinations = set()
                
                for i in range(start_idx, len(schedule_list)):
                    train = schedule_list[i]
                    
                    # (최적화) 현재 시간보다 30분 이상 더 기다려야 하는 열차는 굳이 안 봐도 됨 (선택사항)
                    if train['dept_time'] - current_time > 1800: 
                        break

                    dest_code = train['dest_code']
                    
                    # 이 목적지로 가는 열차를 이미 확인했으면 스킵 (가장 빠른거 하나만 타면 됨)
                    if dest_code in visited_destinations:
                        continue
                        
                    visited_destinations.add(dest_code)
                    
                    arrival_time = train['arr_time']
                    
                    # 큐에 추가 (열차 이동)
                    if dest_code not in min_times or min_times[dest_code] > arrival_time:
                        min_times[dest_code] = arrival_time
                        
                        new_path = path_history + [{
                            "station": train['dest_name'],
                            "code": dest_code,
                            "line": train['line'],
                            "train_code": train['train_code'],
                            "time": self._seconds_to_str(arrival_time),
                            "type": "MOVE" # 열차 이동
                        }]
                        heapq.heappush(pq, (arrival_time, dest_code, new_path))

            # --- [행동 2: 환승 (도보 이동)] ---
            # transfer_list.json을 사용 (Key: st_code)
            if current_code in self.transfers:
                transfer_info = self.transfers[current_code]
                
                for key, val in transfer_info.items():
                    # key format: "1:4" (1호선에서 4호선으로)
                    from_line_chk, to_line_chk = key.split(':')
                    
                    # 현재 내가 있는 호선과 데이터상의 출발 호선이 맞는지 확인 (데이터 무결성)
                    # 데이터 전처리에서 from_line을 정확히 처리했다면 굳이 안 해도 되지만 안전하게.
                    
                    # 목표 호선의 역 코드 찾기
                    # self.station_group['서울역']['4'] -> '0426'
                    target_code = self.station_group[current_name].get(to_line_chk)
                    
                    if target_code:
                        walk_time = val['walk_sec']
                        # 환승 완료 시간
                        transfer_arrival_time = current_time + walk_time
                        
                        if target_code not in min_times or min_times[target_code] > transfer_arrival_time:
                            min_times[target_code] = transfer_arrival_time
                            
                            new_path = path_history + [{
                                "station": current_name,
                                "code": target_code,
                                "line": to_line_chk,
                                "time": self._seconds_to_str(transfer_arrival_time),
                                "walk_distance": val['walk_distance'],
                                "type": "TRANSFER" # 환승
                            }]
                            heapq.heappush(pq, (transfer_arrival_time, target_code, new_path))

        return {"status": "fail", "message": "경로를 찾을 수 없습니다."}

if __name__ == "__main__":
    # 테스트 코드
    pathfinder = SubwayPathfinder() # 기본 평일(weekday) 로드
    
    print("\n--- 🚉 지하철 길찾기 테스트 ---")
    start = input("출발역 입력 (예: 서울역): ").strip()
    end = input("도착역 입력 (예: 강남): ").strip()
    time_input = input("출발 시간 (HH:MM): ").strip()
    
    start_time = time.time()
    result = pathfinder.find_path(start, end, time_input)
    end_time = time.time()
    
    if result['status'] == 'success':
        print("\n✅ 경로 탐색 성공!")
        print(f"총 소요 시간: {result['duration_min']}분 {result['duration_sec']}초")
        print(f"출발: {result['departure_time']} -> 도착: {result['arrival_time']}")
        print("-" * 30)
        
        for step in result['path']:
            action = step['type']
            time_str = step['time']
            name = step['station']
            line = step['line']
            
            if action == 'START':
                print(f"[{time_str}] {name}({line})에서 출발")
            elif action == 'MOVE':
                print(f"  ↓ (지하철 이동)")
                print(f"[{time_str}] {name}({line}) 도착")
            elif action == 'TRANSFER':
                dist = step.get('walk_distance', 0)
                print(f"  ↓ (🚶 환승 도보 {dist}m)")
                print(f"[{time_str}] {name}({line}) 환승 완료")
                
    else:
        print(f"\n❌ 실패: {result.get('message', '알 수 없는 오류')}")

    print(f"\n(알고리즘 소요 시간: {end_time - start_time:.4f}초)")