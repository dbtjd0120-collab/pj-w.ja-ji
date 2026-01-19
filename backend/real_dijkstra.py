import os
import json
import heapq
from datetime import datetime

# -------------------------
# 경로 설정
# -------------------------
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(current_file)
project_root = os.path.dirname(backend_dir)
DATA_DIR = os.path.join(project_root, 'data', 'processed')


class SubwayPathfinder:
    def __init__(self):
        self.day_type = self._get_today_type()
        self._load_data()

    # -------------------------
    # 요일 판단
    # -------------------------
    def _get_today_type(self):
        d = datetime.now().weekday()
        if d < 5:
            return "weekday"
        elif d == 5:
            return "saturday"
        return "holiday"

    # -------------------------
    # 데이터 로드
    # -------------------------
    def _load_data(self):
        graph_file = {
            "weekday": "graph_weekday.json",
            "saturday": "graph_saturday.json",
            "holiday": "graph_holiday.json"
        }[self.day_type]

        with open(os.path.join(DATA_DIR, graph_file), encoding="EUC-KR") as f:
            self.graph = json.load(f)

        with open(os.path.join(DATA_DIR, "transfer_list.json"), encoding="EUC-KR") as f:
            self.transfers = json.load(f)

        with open(os.path.join(DATA_DIR, "stations_list.json"), encoding="EUC-KR") as f:
            self.stations = json.load(f)

        self.station_code_to_name = {
            s["역사코드"]: s["역사명"] for s in self.stations
        }

    # -------------------------
    # 시간 변환
    # -------------------------
    def _time_str_to_sec(self, t):
        h, m = map(int, t.split(":"))
        return h * 3600 + m * 60

    def _sec_to_time(self, sec):
        sec %= 86400
        return f"{sec//3600:02d}:{(sec%3600)//60:02d}"

    # -------------------------
    # 출발 상태 생성
    # -------------------------
    def _get_start_states(self, start_name):
        states = []

        for st in self.stations:
            if st["역사명"] != start_name:
                continue

            code = st["역사코드"]
            line = st["호선"]

            states.append((code, line, False))

            has_express = any(
                e["line"] == line and e.get("express", 0) == 1
                for e in self.graph.get(code, [])
            )
            if has_express:
                states.append((code, line, True))

        if not states:
            raise ValueError(f"출발역 '{start_name}'을 찾을 수 없습니다.")

        return states

    # -------------------------
    # 최단 경로 탐색
    # -------------------------
    def find_path(self, start_name, end_name, start_time):
        start_states = self._get_start_states(start_name)

        pq = []
        dist = {}
        prev = {}
        end_candidates = []

        MAX_WAIT = 3600  # 1시간

        for s in start_states:
            dist[s] = 0
            prev[s] = None
            heapq.heappush(pq, (0, s))

        while pq:
            cost, state = heapq.heappop(pq)
            station, line, is_express = state

            if cost > dist[state]:
                continue

            current_time = start_time + cost

            # 🎯 도착 후보 수집 (즉시 종료 ❌)
            if self.station_code_to_name[station] == end_name:
                end_candidates.append((cost, state))
                continue

            # 1️⃣ 열차 이동
            for e in self.graph.get(station, []):
                if e["line"] != line:
                    continue
                if bool(e["express"]) != is_express:
                    continue
                if e["dept_time"] < current_time:
                    continue
                if e["dept_time"] - current_time > MAX_WAIT:
                    continue

                wait = e["dept_time"] - current_time
                travel = e["arr_time"] - e["dept_time"]
                next_cost = cost + wait + travel
                next_state = (e["dest_code"], line, is_express)

                if next_state not in dist or next_cost < dist[next_state]:
                    dist[next_state] = next_cost
                    prev[next_state] = (state, {
                        "type": "move",
                        "from": station,
                        "to": e["dest_code"],
                        "line": line,
                        "express": is_express
                    })
                    heapq.heappush(pq, (next_cost, next_state))

            # 2️⃣ 환승
            if station in self.transfers:
                for k, info in self.transfers[station].items():
                    from_line, to_line = k.split(":")
                    if from_line != line:
                        continue

                    next_state = (station, to_line, False)
                    next_cost = cost + info["walk_sec"]

                    if next_state not in dist or next_cost < dist[next_state]:
                        dist[next_state] = next_cost
                        prev[next_state] = (state, {
                            "type": "transfer",
                            "from_line": from_line,
                            "to_line": to_line,
                            "time": info["walk_sec"]
                        })
                        heapq.heappush(pq, (next_cost, next_state))

                        # 🔥 환승 후 급행도 즉시 후보로 추가
                        express_state = (station, to_line, True)
                        if express_state not in dist:
                            dist[express_state] = next_cost
                            prev[express_state] = (next_state, {
                                "type": "express_switch",
                                "line": to_line
                            })
                            heapq.heappush(pq, (next_cost, express_state))

            # 3️⃣ 일반 → 급행 전환
            if not is_express:
                for e in self.graph.get(station, []):
                    if e["line"] == line and e["express"] == 1 and e["dept_time"] >= current_time:
                        next_state = (station, line, True)
                        if next_state not in dist or cost < dist[next_state]:
                            dist[next_state] = cost
                            prev[next_state] = (state, {
                                "type": "express_switch",
                                "line": line
                            })
                            heapq.heappush(pq, (cost, next_state))
                        break

        if not end_candidates:
            return None

        best_cost, best_state = min(end_candidates, key=lambda x: x[0])
        return self._build_result(best_state, best_cost, prev, start_time)

    # -------------------------
    # 결과 구성
    # -------------------------
    def _build_result(self, end_state, cost, prev, start_time):
        path = []
        cur = end_state

        while prev[cur]:
            cur, info = prev[cur]
            path.append(info)

        path.reverse()
        return {
            "총소요시간(분)": round(cost / 60, 1),
            "도착시각": self._sec_to_time(start_time + cost),
            "경로": path
        }

    def print_result(self, result):
        print(f"\n🚉 총 소요 시간: {result['총소요시간(분)']}분")
        print(f"🕒 도착 시각: {result['도착시각']}")
        print("\n📍 이동 경로")

        for s in result["경로"]:
            if s["type"] == "move":
                train = "🚄 급행" if s["express"] else "🚇 일반"
                print(f"- {self.station_code_to_name[s['from']]} → "
                      f"{self.station_code_to_name[s['to']]} "
                      f"({s['line']}호선 {train})")
            elif s["type"] == "transfer":
                print(f"- 🔁 환승: {s['from_line']} → {s['to_line']} ({s['time']}초)")
            elif s["type"] == "express_switch":
                print(f"- ⚡ 급행 전환 ({s['line']}호선)")


# -------------------------
# 실행부
# -------------------------
def main():
    print("🚇 지하철 최단경로 탐색기")

    start = input("출발역: ").strip()
    end = input("도착역: ").strip()
    t = input("출발 시각 (HH:MM, Enter 시 현재 시각): ").strip()

    pf = SubwayPathfinder()

    if t:
        start_time = pf._time_str_to_sec(t)
    else:
        now = datetime.now()
        start_time = now.hour * 3600 + now.minute * 60

    result = pf.find_path(start, end, start_time)

    if not result:
        print("❌ 경로를 찾을 수 없습니다.")
        return

    pf.print_result(result)


if __name__ == "__main__":
    main()
