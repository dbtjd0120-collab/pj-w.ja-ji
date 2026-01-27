import os
import pandas as pd
import json


current_file = os.path.abspath(__file__)
backend_file = os.path.dirname(current_file)
project_file = os.path.dirname(backend_file)

Timetable_path = os.path.join(project_file,"data","raw","timetable_sample.csv")
Transfer_path = os.path.join(project_file,"data","processed","transfer_list.json")
df = pd.read_csv(Timetable_path,encoding = "euc-kr")

from datetime import datetime
time_str = input("출발 시간을 입력하세요 (Enter입력시 현재 시간 입력) (HH:MM) : ")
if time_str == "":
    now = datetime.now()
    h = now.hour
    m = now.minute
else:
    h , m = map(int,time_str.split(":"))

while h > 24 or m > 60:
    time_str = input("다시 입력하시오(H < 25)/(M < 60) (HH:MM) : ")
    h , m = map(int,time_str.split(":"))
    
cur_time = 60*h + m

def time_to_second(t):
    if pd.isna(t):
        return None
    if not isinstance(t, str):
        return None

    h, m, s = map(int, t.split(":"))
    return h*3600 + m*60 + s

df["arr_sec"] = df["열차도착시간"].apply(time_to_second)
df["dep_sec"] = df["열차출발시간"].apply(time_to_second)
df_sorted = df.sort_values(
    by = ["열차코드","방향","열차도착시간"]
)
from collections import defaultdict

graph = defaultdict(list)
station_name_to_code = {}

for train_id, group in df.groupby("열차코드"):

    group = group.sort_values("열차출발시간")

    rows = group.to_dict("records")

    for i in range(len(rows) - 1):
        cur = rows[i]
        nxt = rows[i+1]

        from_node = cur["역사코드"]
        to_node = nxt["역사코드"]
        name = cur["역사명"]
        code = int(from_node)
        station_name_to_code[name] = code

        dep_time = time_to_second(cur["열차출발시간"])
        arr_time = time_to_second(nxt["열차도착시간"])

        if dep_time is None or arr_time is None:
            continue

        travel_time = arr_time - dep_time

        edge = {
            "to": to_node,
            "name":name,
            "line": cur["호선"],
            "type": "train",
            "is_express": cur["급행여부"],
            "dep_time": dep_time,
            "travel_time": travel_time
        }

        graph[from_node].append(edge)

df_dep = df[["역사코드", "dep_sec"]]
df_dep = df_dep.dropna(subset=["dep_sec"])
dep_time_by_station = (
    df_dep
    .groupby("역사코드")["dep_sec"]
    .apply(list)
    .to_dict()
)
df_small = df[["역사코드", "arr_sec"]]
df_small = df_small.dropna(subset=["arr_sec"])

arr_time_by_station = (
    df_small
    .groupby("역사코드")["arr_sec"]
    .apply(list)
    .to_dict()
)
with open(os.path.join(Transfer_path), 'r', encoding='EUC-KR') as f:
        transfers = json.load(f)

def add_transfer_edges(graph, transfer_data):
    for from_station, connections in transfer_data.items():
        from_node = int(from_station)

        # 그래프에 노드 없으면 생성
        if from_node not in graph:
            graph[from_node] = []

        for to_station, info in connections.items():
            to_node = int(to_station)

            edge = {
                "to": to_node,
                "type": "transfer",
                "walk_time": info["walk_sec"],
            }

            graph[from_node].append(edge)
    
add_transfer_edges(graph,transfers)


def station_name_to_station_code(name, mapping):
    if name not in mapping:
        raise ValueError(f"존재하지 않는 역입니다: {name}")
    return mapping[name]

start_name = input("출발역을 입력하세요: ")
end_name = input("도착역을 입력하세요: ")

start = station_name_to_station_code(start_name, station_name_to_code)
end = station_name_to_station_code(end_name, station_name_to_code)



def get_next_train(dep_list, cur_time):
    dep_list = sorted([dep_list])

    for d in dep_list:
        if d >= cur_time:
            return d

    # 오늘 막차 끝났으면 → 다음날 첫차
    return dep_list[0] + 24*3600

import heapq


def dijkstra(graph,start,cur_time):
    #1. 거리 테이블 초기화
    INF = (10**9,10**9)
    dist = {node: INF for node in graph}
    dist[start] = (0,cur_time)
    


    #2. 우선순위 큐 (거리,노드)
    pq = []
    heapq.heappush(pq,((0,cur_time),start,None))
    
    #3. 경로 복원을 위한 이전 노드 저장
    prev = {}

    #4. 다익스트라 시작
    while pq:
        #dict(pq)가 완전히 처리할 내용이 없을때까지 계속 반복
      
        (cur_transfer,cur_time), cur_node,prev_line = heapq.heappop(pq)

        #이미 더 짧은 경로가 있으면 스킵
        if (cur_transfer,cur_time) > dist[cur_node]:
            #만약 이 조건이 맞다면 while문의 다음 반복으로 넘어가라는 이야기
            continue
        # 현재 노드에서 갈 수 있는 곳들 확인
        for edge in graph[cur_node]:
           
            
            next_node = edge["to"]
            add_transfer = 0
            type = edge["type"]

            if type == "train":
                travel_time = edge["travel_time"]
                train_is_express = edge["is_express"]
                next_line = edge["line"]
                dep_list = edge["dep_time"]
                next_train_time = get_next_train(dep_list,cur_time)
                new_transfer = cur_transfer
                
                if next_train_time is None:
                     continue
                new_time = next_train_time + travel_time
                wait_time = next_train_time - cur_time
            else:
                 walk_time = edge["walk_time"]
                 new_time = cur_time + walk_time
                 new_transfer = cur_transfer + 1

            new_cost = (new_transfer, new_time)
            # 더 짧은 경로 발견 시 갱신

            if new_cost < dist[next_node]:
                dist[next_node] = new_cost
                prev[next_node] = (cur_node,type)
            
                
                heapq.heappush(pq,(new_cost,next_node,next_line))
            

    return dist,prev
#경로 복원 함수
def get_path(prev,start,end):
    path=[]
    cur = end
    #도착지에서부터 거꾸러 되짚어 볼거임
    while cur != start:
        prev_node , edge_type = prev[cur]
        if edge_type == "transfer":
             #출발역에서 도착할때까지 반복
            path.append(cur)
            path.append("(환승)")
        else:
             path.append(cur)

        #현재 노드를 경로에 추가
        cur = prev_node
        #최단 경로일때 뒤로 한칸 이동 ("D"였을 경우 "B"로 이동)
        #만약 cur == "D"/ prev["D"] = "B" -> cur = "B"

    path.append(start)
    path.reverse()
    return path




dist, prev = dijkstra(graph, start,cur_time)
path = get_path(prev,start, end)

total_arr = int(dist[end][1])
day =total_arr//1440
Ah = total_arr//60
Am = total_arr%60

if Am < m:
    Ah = Ah - 1
    Am = Am + 60
    print("걸린 시간: ", Ah - h,":",Am - m)
    Ah = Ah + 1
    Am = Am - 60
else:
    print("걸린 시간: ", Ah - h,":",Am - m)

if Ah >= 24:
    Ah = Ah - 24


print("환승 횟수: ",dist[end][0])
print("경로:"," -> ".join(path))

print("출발 시간:  ", h , ":" , m)
if day >= 1:
    print("도착 시간:  ", "다음날", Ah, ":", Am)
else:
    print("도착 시간:  ", Ah, ":", Am)

