""" 노드 형태
            (3분, 급행)      [I]—2분—[J]
          /           \   /
[A]—2분—[B]—2분—[C]—2분—[D]—2분—[E]—2분—[F]
                       /
            [G]—2분—[H]
"""

graph = {
    "A":[{"to":"B","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[0,5,10,15,20,25,30,35,40,45,50,55]}],
    "B":[{"to":"A","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[3,8,13,18,23,28,33,38,43,48,53,58]},
         {"to":"C","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[4,9,14,19,24,29,34,39,44,49,54,59]},
         {"to":"D1","travel_time":3,"is_express":"True","line":"1호선","type":"train","dep_time":[10,20,30,40,50]}],
    "C":[{"to":"D1","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[1,11,18,22,28,32,41,51,58]},
         {"to":"B","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[2,8,13,19,21,25,30,35,40,43,48,55]}],
    "D1":[{"to":"B","travel_time":3,"is_express":"True","line":"1호선","type":"train","dep_time":[5,15,25,35,45,55]},
          {"to":"C","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[3,8,12,18,23,29,36,38,41,48,52,59]},
          {"to":"E","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[2,8,19,25,32,40,45,50,55]},
          {"to":"D2","walk_time":1,"type":"transfer"}],
    "D2":[{"to":"D1","walk_time":1,"type":"transfer"},
         {"to":"I","travel_time":2,"is_express":"False","line":"2호선","type":"train","dep_time":[12, 19, 27, 33, 41, 48, 52, 55, 59]},
         {"to":"H","travel_time":2,"is_express":"False","line":"2호선","type":"train","dep_time":[4, 15, 22, 31, 38, 43, 50, 56, 59]}],
    "E":[{"to":"D1","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[7, 13, 25, 29, 34, 46, 51, 57, 58]},
         {"to":"F","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[2, 11, 18, 23, 30, 42, 45, 53, 54]}],
    "F":[{"to":"E","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[9, 14, 21, 28, 36, 40, 47, 55, 59]}],
    "I":[{"to":"D2","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[5, 8, 16, 24, 32, 39, 44, 49, 57]},
         {"to":"J","travel_time":2,"is_express":"False","line":"2호선","type":"train","dep_time":[3, 10, 17, 26, 35, 41, 52, 56]}],
    "J":[{"to":"I","travel_time":2,"is_express":"False","line":"2호선","type":"train","dep_time":[6, 12, 18, 22, 37, 43, 49, 54, 58]}],
    "H":[{"to":"D2","travel_time":2,"is_express":"False","line":"1호선","type":"train","dep_time":[2, 10, 15, 27, 31, 39, 45, 51, 56]},
         {"to":"G","travel_time":2,"is_express":"False","line":"2호선","type":"train","dep_time":[7, 14, 23, 28, 33, 40, 48, 55, 59]}],
    "G":[{"to":"H","travel_time":2,"is_express":"False","line":"2호선","type":"train","dep_time":[4, 9, 19, 25, 36, 42, 47, 50, 53]}]
}
#환승에 대한 travel_time를 생각해봐야함 (환승이 이점이 되면 안되고 벌점이 되어야함)
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
def get_next_train(dep_list,cur_time):
                for i in range(h,h+24):
                    for d in dep_list:
                        candidate = i*60 + d
                        if candidate >= cur_time:
                            return candidate
                return None

import heapq


def dijkstra(graph,start,cur_time):
    #1. 거리 테이블 초기화
    INF = (10**9,10**9)
    dist = {node: INF for node in graph}
    dist[start] = (0,cur_time)
    


    #2. 우선순위 큐 (거리,노드)
    pq = []
    heapq.heappush(pq,((0,cur_time),start,None))
    '''heapq 설명
    heap는 부모노드가 자식노드보다 무조건 작게 만들게끔
    가장 맨 앞에 나오는 요소가 가장 작은 값을 가질수 있게 만듦
    리스트를 정렬하는게 아닌 최소한의 값을 빠르게 가져오기 위함
    heapq는 리스트를 heap처럼 관리해줌
    '''
    '''heapq.heappush (넣기)설명
    heapq.heappush(pq,value)는 value의 값을 리스트 끝에 추가함

    example)
    pq = []

    heapq.heappush(pq, 5)
    heapq.heappush(pq, 2)
    heapq.heappush(pq, 8)
    heapq.heappush(pq, 1)

    이렇게 되면 pq 리스트 안에 가장 첫번쨰 즉,pq[0]은 1이 된다.
    print(pq) -> [1,2,8,5] (아마도)
    어쨋든간 가장 첫번째는 1
    '''
    '''heapq.heappop (꺼내기)설명
    가장 작은값인 pq[0]을 꺼낸뒤 제거
    
    example)
    min_value = heapq.heappop(pq)일 경우
    min_value는 pq[0]의 값을 갖게 되고 pq[0]은 삭제된다.
    삭제된 이후에 pq는 다시 heap으로 재정렬 된다.

    '''
    '''heappush(pq, (거리, 노드)) 즉 튜플이 들어갈 경우 
        튜플의 첫번째 요소인 거리를 기준으로 heap(최솟값=pq[0])된다
    '''
    #3. 경로 복원을 위한 이전 노드 저장
    prev = {}

    #4. 다익스트라 시작
    while pq:
        #dict(pq)가 완전히 처리할 내용이 없을때까지 계속 반복
        '''pq 변화
        초기        → [(0, A)]
        A 처리 후   → [(2, B)]
        B 처리 후   → [(3, D), (4, C)]
        D 처리 후   → [(4, C), (5, E)]
        C 처리 후   → [(5, E)]
        E 처리 후   → []
        ''' 
        (cur_transfer,cur_time), cur_node,prev_line = heapq.heappop(pq)

        #이미 더 짧은 경로가 있으면 스킵
        if (cur_transfer,cur_time) > dist[cur_node]:
            #만약 이 조건이 맞다면 while문의 다음 반복으로 넘어가라는 이야기
            continue
        # 현재 노드에서 갈 수 있는 곳들 확인
        for edge in graph[cur_node]:
            '''edge 역할
            edge는 graph[cur_node]의 딕셔너리를 가져옴
            example)
            for edge in graph["B"]:
            일 경우 edge는 graph["B"]의 모든 정보(딕셔너리)를 가져온다.

            '''
            
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
                '''prev[next_node]에 관한 설명
                next_node에 최단 거리로 도달했을 때,
                바로 이전 노드는 cur_node였다
                example) prev = {
                        "B": "A",
                        "D": "B",
                        "E": "D"
                        }    
                '''
                
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

start = input("출발 지점을 입력하세요 : ")
end = input("도착지점을 입력하세요 : ")

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
'''join에 관한 설명

join이란 리스트 안의 문자열들을 하나의 문자열로 이어붙이는 함수
구분자.join(리스트) 를 사용하면 각 요소들 사이에 구분자가 들어가면서 자연스럽게 출력됨
example)
"->".join(["A","B","C","D"]) =>
A -> B -> c -> D
Other)
"-".join(["A","B","C","D"]) =>
A - B - c - D
주의!) 단, path안의 요소는 모두 문자열이여야함
path = ["A", 2, "B"]  # ❌ 에러
 ㄴ 필요하면 map(str,path)

'''
print("출발 시간:  ", h , ":" , m)
if day >= 1:
    print("도착 시간:  ", "다음날", Ah, ":", Am)
else:
    print("도착 시간:  ", Ah, ":", Am)

'''
Ex) 출발 : A
    도착 : G
    출발 시각 : 12:56
    도착 시각 : 13:25
    총 소요시간 : 29    
A - B  
기다리는 시간 4분
이동시간 2분
총 소요시간 6분 
나중 시간 13:02
B - D
기다리는 시간 1분
이동시간 3분 
총 소요시간 4분
나중시간 13:06
D - H
기다리는 시간 9분
이동시간 2분
총 소요시간 11분
나중시간 13:18
H - G
기다리는 시간 5분
이동시간 2분
총 소요시간 7분
나중시간 13:25분

이동시간(travel_time)은 굳이 볼 필요 없고 어짜피 기다리는 시간 + 이동시간이 전체적인 travel_time 이니까 
이렇게 하면 환승하는것도 신경쓸 필요 없음 (환승할때 시간 추가하는 것만 넣으면 됌)
'''

