graph = {
    # 1호선 일반
    ("A", "1"): {("B", "1"): 2},
    ("B", "1"): {("A", "1"): 2, ("C", "1"): 2, ("D", "1"): 3},  # 급행 포함
    ("C", "1"): {("B", "1"): 2, ("D", "1"): 2},
    ("D", "1"): {("C", "1"): 2, ("E", "1"): 2},
    ("E", "1"): {("D", "1"): 2, ("F", "1"): 2},
    ("F", "1"): {("E", "1"): 2},

    # 2호선 일반
    ("G", "2"): {("H", "2"): 2},
    ("H", "2"): {("G", "2"): 2, ("D", "2"): 2},
    ("D", "2"): {("H", "2"): 2, ("I", "2"): 2},
    ("I", "2"): {("D", "2"): 2, ("J", "2"): 2},
    ("J", "2"): {("I", "2"): 2},
}

trans = {
    "B": {
        "1:1": {"w": 1}
    },
    "D": {
        "1:1": {"w": 1},
        "1:2": {"w": 2},
        "2:1": {"w": 3}
    }
}







import heapq

def dijkstra(graph, trans, start_station, start_line, end_station):
    start = (start_station, start_line)

    pq = []
    heapq.heappush(pq, (0, start))

    dist = {start: 0}
    prev = {}

    while pq:
        curr_time, (station, line) = heapq.heappop(pq)

        if curr_time > dist.get((station, line), float("inf")):
            continue

        # 도착역이면 종료 (호선 무관)
        if station == end_station:
            break

        # 1️⃣ 열차 이동
        for (nxt_station, nxt_line), w in graph.get((station, line), {}).items():
            new_time = curr_time + w
            nxt_state = (nxt_station, nxt_line)

            if new_time < dist.get(nxt_state, float("inf")):
                dist[nxt_state] = new_time
                prev[nxt_state] = (station, line)
                heapq.heappush(pq, (new_time, nxt_state))

        # 2️⃣ 대기 / 환승 (trans)
        if station in trans:
            for key, info in trans[station].items():
                from_line, to_line = key.split(":")
                if from_line == line:
                    wait_time = info["w"]
                    nxt_state = (station, to_line)
                    new_time = curr_time + wait_time

                    if new_time < dist.get(nxt_state, float("inf")):
                        dist[nxt_state] = new_time
                        prev[nxt_state] = (station, line)
                        heapq.heappush(pq, (new_time, nxt_state))

    # 도착역 후보 중 최단 선택
    candidates = [(state, t) for state, t in dist.items() if state[0] == end_station]
    if not candidates:
        return None, None

    end_state, best_time = min(candidates, key=lambda x: x[1])

    # 경로 복원
    path = []
    cur = end_state
    while cur in prev:
        path.append(cur)
        cur = prev[cur]
    path.append(start)
    path.reverse()

    return path, best_time

def run():
    start_station = input("출발역을 입력하세요: ").strip()
    start_line = input("출발 호선을 입력하세요: ").strip()
    end_station = input("도착역을 입력하세요: ").strip()

    start_state = (start_station, start_line)

    # 출발 상태 검증
    if start_state not in graph:
        print("존재하지 않는 출발역 또는 호선입니다.")
        return

    # 도착역 존재 여부 확인 (호선 무관)
    if not any(st == end_station for (st, _) in graph.keys()):
        print("존재하지 않는 도착역입니다.")
        return

    path, total_time = dijkstra(
        graph,
        trans,
        start_station,
        start_line,
        end_station
    )

    if path is None:
        print("경로를 찾을 수 없습니다.")
        return

    print("\n🚇 최단 시간 경로")
    print(" → ".join(f"{st}({line})" for st, line in path))
    print(f"총 소요 시간: {total_time}분")


if __name__ == "__main__":
    run()

