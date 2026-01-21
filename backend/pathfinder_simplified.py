
""" 노선도, 시간표
           -(3분, 급행)-   [I]—2분—[J]
          /            \\ /
[A]—2분—[B]—2분—[C]—2분—[D]—2분—[E]—2분—[F]
                       /
             [G]—2분—[H]

역간 이동시간 2분, 정차 1분, 배차간격 5분, 출발시간 기준으로 작성.

-------------------------------------------

                  A  B  C  D  E  F 
1호선 완행 1호차 | 00 03 06 09 12 15
1호선 완행 2호차 | 05 08 11 14 17 20
1호선 완행 3호차 | 10 13 16 19 22 25
1호선 완행 4호차 | 15 18 21 24 27 30
1호선 완행 5호차 | 20 23 26 29 32 35
1호선 완행 6호차 | 25 28 31 34 37 40
1호선 완행 7호차 | 30 33 36 39 42 45
1호선 완행 8호차 | 35 38 41 44 47 50
1호선 완행 9호차 | 40 43 46 49 52 55

1호선 완행 1호차 | 15 12 09 06 03 00
1호선 완행 2호차 | 20 17 14 11 08 05
1호선 완행 3호차 | 25 22 19 16 13 10
1호선 완행 4호차 | 30 27 24 21 18 15
1호선 완행 5호차 | 35 32 29 26 23 20
1호선 완행 6호차 | 40 37 34 31 28 25
1호선 완행 8호차 | 50 47 44 41 38 35
1호선 완행 9호차 | 55 52 49 46 43 40

1호선 급행 1호차 | 01 04    08 11 14
1호선 급행 2호차 | 11 14    18 21 24
1호선 급행 3호차 | 21 24    28 31 34
1호선 급행 4호차 | 31 34    38 41 44
1호선 급행 5호차 | 41 44    48 51 54

1호선 급행 1호차 | 14 11    08 04 01
1호선 급행 2호차 | 24 21    18 14 11
1호선 급행 3호차 | 34 31    28 24 21
1호선 급행 4호차 | 44 41    38 34 31
1호선 급행 5호차 | 54 51    48 44 41

-------------------------------------------

              G    H   D    I    J
2호선 1호차 | 00분 03분 06분 09분 12분
2호선 2호차 | 10분 13분 16분 19분 22분
2호선 3호차 | 20분 23분 26분 29분 32분
2호선 4호차 | 30분 33분 36분 39분 42분
2호선 5호차 | 40분 43분 46분 49분 52분
2호선 6호차 | 45분 48분 51분 54분 57분

2호선 1호차 | 12분 09분 06분 03분 00분
2호선 2호차 | 22분 19분 16분 13분 10분
2호선 3호차 | 32분 29분 26분 23분 20분
2호선 4호차 | 42분 39분 36분 33분 30분
2호선 5호차 | 52분 49분 46분 43분 40분
2호선 6호차 | 57분 54분 51분 48분 45분

"""

import heapq

graph = {
    "A":[{"to":"B","travel_time":2,"is_express":False,"line":"1호선","dep_time":[0, 5, 10, 15, 20, 25, 30, 35, 40]},
         {"to":"B","travel_time":2,"is_express":True,"line":"1호선","dep_time":[1, 11, 21, 31, 41]}],
    "B":[{"to":"A","travel_time":2,"is_express":False,"line":"1호선","dep_time":[12, 17, 22, 27, 32, 37, 42, 47, 52]},
         {"to":"C","travel_time":2,"is_express":False,"line":"1호선","dep_time":[3, 8, 13, 18, 23, 28, 33, 38, 43]},
         {"to":"D1","travel_time":3,"is_express":True,"line":"1호선","dep_time":[4, 14, 24, 34, 44]}],
    "C":[{"to":"B","travel_time":2,"is_express":False,"line":"1호선","dep_time":[9, 14, 19, 24, 29, 34, 39, 44, 49]},
         {"to":"D1","travel_time":2,"is_express":False,"line":"1호선","dep_time":[6, 11, 16, 21, 26, 31, 36, 41, 46]}],
    "D1":[{"to":"C","travel_time":2,"is_express":False,"line":"1호선","dep_time":[6, 11, 16, 21, 26, 31, 36, 41, 46]},
         {"to":"B","travel_time":3,"is_express":True,"line":"1호선","dep_time":[8, 18, 28, 38, 48]},
         {"to":"E","travel_time":2,"is_express":False,"line":"1호선","dep_time":[9, 14, 19, 24, 29, 34, 39, 44, 49]},
         {"to":"E","travel_time":2,"is_express":True,"line":"1호선","dep_time":[8, 18, 28, 38, 48]},
         {"to":"D2","travel_time":1,"is_express":False,"line":"trs"}],
    "D2":[{"to":"H","travel_time":2,"is_express":False,"line":"2호선","dep_time":[6, 16, 26, 36, 46, 51]},
         {"to":"I","travel_time":2,"is_express":False,"line":"2호선","dep_time":[6, 16, 26, 36, 46, 51]},
         {"to":"D1","travel_time":1,"is_express":False,"line":"trs"}],
    "E":[{"to":"D1","travel_time":2,"is_express":False,"line":"1호선","dep_time":[3, 8, 13, 18, 23, 28, 33, 38, 43]},
         {"to":"F","travel_time":2,"is_express":False,"line":"1호선","dep_time":[12, 17, 22, 27, 32, 37, 42, 47, 52]},
         {"to":"F","travel_time":2,"is_express":True,"line":"1호선","dep_time":[11, 21, 31, 41, 51]}],
    "F":[{"to":"E","travel_time":2,"is_express":False,"line":"1호선","dep_time":[0, 5, 10, 15, 20, 25, 30, 35, 40]},
         {"to":"E","travel_time":2,"is_express":True,"line":"1호선","dep_time":[1, 11, 21, 31, 41]}],
    "G":[{"to":"H","travel_time":2,"is_express":False,"line":"2호선","dep_time":[0, 10, 20, 30, 40, 45]}],
    "H":[{"to":"D2","travel_time":2,"is_express":False,"line":"2호선","dep_time":[3, 13, 23, 33, 43, 48]},
         {"to":"G","travel_time":2,"is_express":False,"line":"2호선","dep_time":[9, 19, 29, 39, 49, 54]}],
    "I":[{"to":"D2","travel_time":2,"is_express":False,"line":"2호선","dep_time":[3, 13, 23, 33, 43, 48]},
         {"to":"J","travel_time":2,"is_express":False,"line":"2호선","dep_time":[9, 19, 29, 39, 49, 54]}],
    "J":[{"to":"I","travel_time":2,"is_express":False,"line":"2호선","dep_time":[0, 10, 20, 30, 40, 45]}],
}


def djikstra(start, start_minutes, mode = 0):
    init_priority = (start_minutes, 0) if mode == 0 else (0, start_minutes)
    cost = {node: (float('inf'), float('inf')) for node in graph}
    cost[start] = init_priority

    pq = [(init_priority, start)]
    navi_log = {}

    while pq:
        curr_priority, cur_node = heapq.heappop(pq)
        if mode == 0:
            cur_time, trs_count = curr_priority
        else:
            trs_count, cur_time = curr_priority

        if curr_priority > cost[cur_node]: continue  # 우선순위 튜플 자체를 비교

        for edge in graph[cur_node]:
            next_node = edge['to']

            # 다음 열차 출발시각 확인
            dep_time = _get_next_train(edge, cur_time)
            if dep_time is ValueError: continue      # 다음 열차가 없는 경우 다음 반복으로 진행

            # 도착시간 및 환승 횟수 계산
            if edge["line"] == "trs":
                arrival_time = cur_time + edge["travel_time"]
                new_trs_count = trs_count + 1
            else:
                arrival_time = dep_time + edge["travel_time"]
                new_trs_count = trs_count

            # 새로운 우선순위 생성
            new_priority = (arrival_time, new_trs_count) if mode == 0 else (new_trs_count, arrival_time)
            
            # 새로운 우선순위와 기존 cost 비교 후 heappush
            if new_priority < cost[next_node]:
                cost[next_node] = new_priority
                navi_log[next_node] = (cur_node, edge['travel_time'], edge["line"], edge["is_express"])
                heapq.heappush(pq,(new_priority, next_node))
                """다음역:출발역, 다다음역:다음역"""

    return cost, navi_log

def _get_next_train(edge, cur_time):
    if 'dep_time' not in edge: return cur_time
    for dep_time in edge['dep_time']:
        if dep_time >= cur_time:
            return dep_time
    return ValueError

def print_route_details(navi_log, start, end, cost, mode=0):
    if end not in navi_log:
        print(f"\n[{'최단 시간' if mode==0 else '최소 환승'}] 경로를 찾을 수 없습니다.")
        return

    if mode == 0: total_time , trs_count = cost[end]
    else: trs_count, total_time = cost[end]
    if mode == 0: start_minutes , _ = cost[start]
    else: _, start_minutes = cost[start]

    # 경로 역추적 리스트 생성
    path = []
    full_path = []
    curr = end

    while curr != start:
        # 이전 역, 이동시간, 타고온 호선, 급행 여부를 받음.
        prev, travel_time, line, is_exp = navi_log[curr]
        path.append({
            "from": prev,
            "to": curr,
            "time": travel_time,
            "line": line,
            "is_exp": is_exp
        })
        full_path.append(curr)
        curr = prev

    full_path.append(start)
    path.reverse()
    full_path.reverse()

    details = []

    details.append(f"[{path[0]['from']}")
    st_count = 0
    duration = 0
    for i in range(0, len(path)-1):
        if path[i]['line'] != "trs":
            details.append(f" -> {path[i]['to']}")
            st_count += 1
            duration += path[i]['time']
            continue

        if path[i]['line'] == "trs":
            exp_tag = "(급행)" if path[i]["is_exp"] else ""
            details.append(f"] {path[i-1]['line']}{exp_tag}, {st_count}개 역 이동, {duration}분 소요")
            st_count = 0
            duration = 0
            details.append(f"\n[{path[i]['from']} -> {path[i]['to']}] 환승, 도보 {path[i]['time']}분 소요")
            details.append(f"\n[{path[i]['to']}")
            continue

    exp_tag = "(급행)" if path[-1]["is_exp"] else ""
    details.append(f" -> {path[-1]['to']}")
    details.append(f"] {path[-1]['line']}{exp_tag}, {st_count}개 역 이동, {duration}분 소요")

    print(f"\n[{'최단 시간' if mode==0 else '최소 환승'}] 경로: {' -> '.join(full_path)} | {total_time}분 도착 예정 ({total_time - start_minutes}분 소요) | 환승: {trs_count}번")
    # 소요시간 출력부 수정 필요 -> cost는 튜플형태.
    print("-" * 40)
    for detail in details:
        print(detail, end="")
    print("\n", "-" * 40)


def format_path_line(nodes, line, is_exp, duration):
    """[역1 -> 역2 -> 역3] 호선명(급행), 00분 소요 형식으로 변환"""
    path_str = " -> ".join(nodes)
    exp_tag = "(급행)" if is_exp else ""
    
    if line == "trs":
        return f"[{path_str}] 환승, 도보 {duration}분 소요"
    return f"[{path_str}] {line}{exp_tag}, {duration}분 소요"



if __name__ == "__main__":
    print("-------------- 지하철 노선도 --------------")
    print("           -(3분, 급행)-   [I]—2분—[J]")
    print("          /             \\ /") 
    print("[A]—2분—[B]—2분—[C]—2분—[D]—2분—[E]—2분—[F]")
    print("                        /")
    print("              [G]—2분—[H]")

    m = int(input("\n출발 분 입력 (MM) (0 ≤ M < 60) : "))
    while m > 59 or m < 0:
        m = int(input("형식에 맞게 다시 입력하세요. (MM) (0 ≤ M < 60) : "))
        
    start = input("출발역 입력: ").strip()
    end = input("도착역 입력: ").strip()
    
    cost, navi_log = djikstra(start, m, 0)      # 최단시간
    path = print_route_details(navi_log, start, end, cost, 0)
    cost, navi_log = djikstra(start, m, 1)      # 최소환승
    path = print_route_details(navi_log, start, end, cost, 1)

