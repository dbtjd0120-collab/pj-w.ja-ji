import os
from datetime import datetime
import json
import heapq
import time

current_file = os.path.abspath(__file__)        # 파일 절대경로 계산
backend_dir = os.path.dirname(current_file)     # 상위폴더로 이동
project_root = os.path.dirname(backend_dir)     # 상취 폴더로 이동

TIMETABLE_PATH = os.path.join(project_root, 'data', 'raw', 'timetable.csv')
TRANSFER_PATH = os.path.join(project_root, 'data', 'raw', 'transfer_info.csv')
OUTPUT_DIR = os.path.join(project_root, 'data', 'processed', '')

class Pathfinder:
    def __init__(self, in_day):
        self.day_type = self._get_today_type(in_day)
        print(f"운행구분 : {self.day_type}")
        self._load_data()

    def _get_today_type(self, in_day):  # 날짜를 요일로
        day_dict = {5: 'saturday', 6: 'holiday'}
        return day_dict.get(in_day, 'weekday')

    def _load_data(self):
        # 컴프리헨션 사용
        try:
            with open(f"{OUTPUT_DIR}graph_{self.day_type}.json", 'r', encoding='EUC-KR') as f:
                raw_graph = json.load(f)
                self.graph = {
                    int(a_code): {
                        int(b_code): schedules 
                        for b_code, schedules in dest_dict.items()
                    }
                    for a_code, dest_dict in raw_graph.items()
                }
            with open(f"{OUTPUT_DIR}transfer_list.json", 'r', encoding='EUC-KR') as f:
                self.raw_trs = json.load(f)
                self.transfer_list = {
                    int(a_code): {
                        int(b_code): trs_info
                        for b_code, trs_info in trs_dict.items()
                    }
                    for a_code, trs_dict in self.raw_trs.items()
                }
            with open(f"{OUTPUT_DIR}stations_list.json", 'r', encoding='EUC-KR') as f:
                self.raw_st = json.load(f)
                self.name_to_code = {
                    name: [int(code) for code in codes]
                    for name, codes in self.raw_st.items()
                }
                self.code_to_name = {
                    int(code): name 
                    for name, codes in self.raw_st.items() 
                    for code in codes
                }
        except Exception as e:
            print(f"로딩 실패. (오류 코드: {e})")
            exit()

    def search(self, start, end, start_time):
        parts = list(map(int, str(start_time).split(':')))
        start_sec = parts[0] * 3600 + parts[1]*60


        # 출발역 
        cost, navi_log = self.djikstra(start, start_sec, 0)
        self.print_route_details(navi_log, start, end, cost, 0)
        cost, navi_log = self.djikstra(start, start_sec, 1)
        self.print_route_details(navi_log, start, end, cost, 1)

    def djikstra(self, start, start_sec, mode = 0):
        p_start = time.time()
        init_priority = (start_sec, 0) if mode == 0 else (0, start_sec)

        # cost = {node: (float('inf'), float('inf')) for node in self.graph}
        # 기존엔 다 넣고 가봤지만, 이번엔 호출되기 직전에만 투입됨.
        # 어차피 다 투입될지도 모르니까 해보고 나중에 별 상관 없으면 복구.
        cost = {node: (float('inf'), float('inf')) for node in self.graph}
        pq = []
        navi_log = {}

        start_codes = self.name_to_code.get(start)
        if not start_codes:
            print(f"'{start}'은(는) 존재하지 않는 역 이름입니다.")
            return None, None

        # for start_code in self.name_to_code[start]:
        # 로만 하면 start가 name_to_code에 없을 시 그냥 에러뱉고 오류남.
        for start_code in start_codes:
            heapq.heappush(pq, (init_priority, start_code))
            cost[start_code] = init_priority

        while pq:
            curr_priority, cur_code = heapq.heappop(pq)
            if mode == 0: cur_time, trs_count = curr_priority
            else: trs_count, cur_time = curr_priority

            if curr_priority > cost[cur_code]: continue  # 우선순위 튜플 자체를 비교

            for next_node, schedule in self.graph[cur_code].items():

                # 다음 열차 출발시각 확인하고 제일 빠른걸 탔을 때 도착시간 구하기
                next_train_info = self._get_next_train(schedule, cur_time)
                if next_train_info is None: continue      # 다음 열차가 없는 경우 다음 반복으로 진행

                # 새로운 우선순위 생성
                new_priority = (next_train_info['arr_time'], trs_count) if mode == 0 else (trs_count, next_train_info['arr_time'])
                
                # 새로운 우선순위와 기존 cost 비교 후 heappush
                if new_priority < cost[next_node]:
                    cost[next_node] = new_priority
                    navi_log[next_node] = (cur_code, next_train_info['arr_time'], next_train_info["is_exp"], next_train_info["line"])
                    heapq.heappush(pq,(new_priority, next_node))
                    """다음역:출발역, 다다음역:다음역"""
            
            if cur_code in self.transfer_list:
                for trs_code, trs_info in self.transfer_list[cur_code].items():
                    arr_time = cur_time + trs_info['walk_sec']
                    new_priority = (arr_time, trs_count + 1) if mode == 0 else (trs_count + 1, arr_time)

                    if new_priority < cost[trs_code]:
                        cost[trs_code] = new_priority
                        navi_log[trs_code] = (cur_code, arr_time, False, "trs")
                        # 이전 역, 현재 역 도착시간, 환승이니까 급행아님, 환승표기 를 기록함.
                        heapq.heappush(pq,(new_priority, trs_code))
                        """다음역:출발역, 다다음역:다음역"""
        p_time = time.time() - p_start
        print(f"\n[다익스트라 알고리즘 시행 시간 : {p_time:.3f}초]")
        return cost, navi_log

    # def _get_next_train(edge, cur_time):
    #     if 'dep_time' not in edge: return cur_time
    #     for dep_time in edge['dep_time']:
    #         if dep_time >= cur_time:
    #             return dep_time
    #     return ValueError

    def _get_next_train(self, schedule, cur_time):
        low, high = 0, len(schedule) - 1
        idx = -1
        while low <= high:
            mid = (low + high) // 2
            if schedule[mid]['dep_time'] >= cur_time:
                idx = mid
                high = mid - 1
            else: low = mid + 1
        return schedule[idx] if idx != -1 else None
        # 다음열차의 딕셔너리 전부를 반환. navi_log 기록시에 사용해야함.

    def print_route_details(self, navi_log, start, end, cost, mode=0):
        if navi_log is None and cost is None:
            print(f"----------경로 탐색 불가----------")
            return

        end_codes = self.name_to_code.get(end)
        actual_end_code = None
        min_cost = (float('inf'), float('inf'))
        for end_code in end_codes:
            if cost[end_code] < min_cost:
                min_cost = cost[end_code]
                actual_end_code = end_code

        if actual_end_code is None:
            print(f"\n[{'최단 시간' if mode==0 else '최소 환승'}] 경로를 찾을 수 없습니다.")
            return

        # 경로 역추적 리스트 생성
        path = []
        curr = actual_end_code
        while curr in navi_log:
            prev, arr_time, is_exp, line = navi_log[curr]
            path.append({"from": prev, "to": curr, "arr_time": arr_time, "is_exp": is_exp, "line": line})
            curr = prev
            # 코드 업로드 시 원래 사용하던 논리로 할 것.
        path.reverse()
        start_code = path[0]['from']

        segments = []
        if path:
            line_seg = {
                "stations": [path[0]['from'], path[0]['to']],
                "end_time": path[0]['arr_time'],
                "is_exp": path[0]['is_exp'],
                "line": path[0]['line']
            }
            
            for i in range(1, len(path)):
                node = path[i]
                # 호선이 같으면 역 목록에 추가만
                if node['line'] == line_seg['line'] and node['is_exp'] == line_seg['is_exp']:
                    line_seg['stations'].append(node['to'])
                    line_seg['end_time'] = node['arr_time']
                elif node['line'] == "trs":
                    segments.append(line_seg)
                    line_seg = {
                        "stations": [node['to']],
                        "end_time": node['arr_time'],
                        "is_exp": node['is_exp'],
                        "line": node['line']
                    }
                else:
                    # 호선이나 급행이 바뀌면 지금까지의 세그먼트 저장 후 새로 시작
                    segments.append(line_seg)
                    line_seg = {
                        "stations": [node['from'], node['to']],
                        "end_time": node['arr_time'],
                        "is_exp": node['is_exp'],
                        "line": node['line']
                    }
            segments.append(line_seg)

        end_sec, trs_count = cost[actual_end_code] if mode == 0 else (cost[actual_end_code][1], cost[actual_end_code][0])
        start_sec = cost[start_code][0] if mode == 0 else cost[start_code][1]
        move_time = self.seconds_to_str(end_sec - start_sec)

        print(f"\n[{'최단 시간' if mode==0 else '최소 환승'} 경로] "
            f"도착 예정: {self.seconds_to_str(end_sec)} ({move_time} 소요) | 환승: {trs_count}회")
        print("-" * 60)

        prev_arr_time = start_sec
        for seg in segments:
            st_names = [self.code_to_name[c] for c in seg['stations']]
            duration = self.seconds_to_str(seg['end_time'] - prev_arr_time)
            
            if seg['line'] == "trs":
                print(f" [환승] {st_names[0]} (도보 {duration})")
            else:
                exp_tag = " (급행)" if seg['is_exp'] else ""
                print(f" [{seg['line']}호선{exp_tag}] {st_names[0]} ➔ {st_names[-1]} ({len(st_names)-1}개 역, {duration}소요)")
                print(f"    └ 경로: {' ➔ '.join(st_names)}")
            
            prev_arr_time = seg['end_time']
        
        print("-" * 60)

    def seconds_to_str(self, seconds):
        """ 초(int) -> 문자열(HH:MM:SS) 변환 """
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02}"




if __name__ == "__main__":#
    while True:
        d = input("날짜 입력 (YY/MM/DD, 오늘이면 엔터): ").strip()
        if not d:
            d = datetime.now().weekday()
            break
        try:
            date_obj = datetime.strptime(d, "%y/%m/%d")
            d = date_obj.weekday()
            break
        except ValueError:
            print("\n형식이 잘못되었습니다. 다시 입력해주세요.")
    finder = Pathfinder(d)
    s = input("출발역 입력 (예: 상수): ").strip()
    e = input("도착역 입력 (예: 공릉): ").strip()
    t = input("출발 시각 입력 (HH:MM): ").strip()
    finder.search(s, e, t)