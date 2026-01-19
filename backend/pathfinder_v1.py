import heapq

"""
           -(3분, 급행)-  [I]—2분—[J]
          /            \ /
[A]—2분—[B]—2분—[C]—2분—[D]—2분—[E]—2분—[F]
                       /
             [G]—2분—[H]
"""
                                 
graph = {
    "A":[{"to":"B","travel_time":2,"is_express":False,"line":"1호선"}],
    "B":[{"to":"A","travel_time":2,"is_express":False,"line":"1호선"},
         {"to":"C","travel_time":2,"is_express":False,"line":"1호선"},
         {"to":"D1","travel_time":3,"is_express":True,"line":"1호선"}],
    "C":[{"to":"B","travel_time":2,"is_express":False,"line":"1호선"},
         {"to":"D1","travel_time":2,"is_express":False,"line":"1호선"}],
    "D1":[{"to":"C","travel_time":2,"is_express":False,"line":"1호선"},
         {"to":"B","travel_time":3,"is_express":True,"line":"1호선"},
         {"to":"E","travel_time":2,"is_express":False,"line":"1호선"},
         {"to":"D2","travel_time":1,"is_express":False,"line":"trs"}],
    "D2":[{"to":"H","travel_time":2,"is_express":False,"line":"2호선"},
         {"to":"I","travel_time":2,"is_express":False,"line":"2호선"},
         {"to":"D1","travel_time":1,"is_express":False,"line":"trs"}],
    "E":[{"to":"D1","travel_time":2,"is_express":False,"line":"1호선"},
         {"to":"F","travel_time":2,"is_express":False,"line":"1호선"}],
    "F":[{"to":"E","travel_time":2,"is_express":False,"line":"1호선"}],
    "G":[{"to":"H","travel_time":2,"is_express":False,"line":"2호선"}],
    "H":[{"to":"D2","travel_time":2,"is_express":False,"line":"2호선"},
         {"to":"G","travel_time":2,"is_express":False,"line":"2호선"}],
    "I":[{"to":"D2","travel_time":2,"is_express":False,"line":"2호선"},
         {"to":"J","travel_time":2,"is_express":False,"line":"2호선"}],
    "J":[{"to":"I","travel_time":2,"is_express":False,"line":"2호선"}],
}
# 방향을 확인하고 이동 시간, 급행, 이동할 호선을 보여줘야 함.
# A -> B -> D1 -> D2 -> I -> J
# D1 -> D2 환승, 도보 1분
# 총 소요시간 10분


def djikstra(start):
    dist = {node:float('inf') for node in graph}
    dist[start] = 0
    pq = []
    heapq.heappush(pq, (0, start))
    path_log = {}

    while pq:
        cur_dist, cur_node = heapq.heappop(pq)

        if cur_dist > dist[cur_node]: continue

        for edge in graph[cur_node]:
            next_node = edge['to']
            cost = edge['travel_time']
            new_dist = cur_dist + cost

            if new_dist < dist[next_node]:
                path_log[next_node] = (cur_node, cost, edge["line"], edge["is_express"])
                dist[next_node] = new_dist
                heapq.heappush(pq,(new_dist,next_node))
                """다음역:출발역, 다다음역:다음역"""

    return dist, path_log

def print_route_details(path_log, start, end, dist):
    path = []
    curr = end
    details = []

    while curr != start:
        prev, time, line, is_exp = path_log[curr]
        # if is_exp: exp_tag = "(급행)" 
        # else: exp_tag = ""
        exp_tag = "(급행)" if is_exp else ""        # 삼항연산자



        if line == "trs":
            details.append(f"[{prev} -> {curr}] 환승, 도보 {time}분")
        else:
            details.append(f"[{prev} -> {curr}] {line}{exp_tag}, {time}분 소요")
        
        path.append(curr)
        curr = prev
    
    path.append(start)
    path.reverse()
    details.reverse()

    print(f"\n 전체 경로: {' -> '.join(path)} | 총 {dist[end]}분 소요")
    print("-" * 40)

    for detail in details:
        print(detail)

if __name__ == "__main__":
    print("-------------- 지하철 노선도 --------------")
    print("           -(3분, 급행)-   [I]—2분—[J]")
    print("          /             \\ /") 
    print("[A]—2분—[B]—2분—[C]—2분—[D]—2분—[E]—2분—[F]")
    print("                        /")
    print("              [G]—2분—[H]")
    start = input("\n출발역 입력: ").strip()
    end = input("도착역 입력: ").strip()
    # time_input = input("출발 시간 (HH:MM): ").strip()
    
    dist, path_log = djikstra(start)
    path = print_route_details(path_log, start, end, dist)

