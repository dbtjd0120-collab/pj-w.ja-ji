""" 노드 형태
            (3분, 급행)      [I]—2분—[J]
          /           \   /
[A]—2분—[B]—2분—[C]—2분—[D]—2분—[E]—2분—[F]
                       /
            [G]—2분—[H]
"""

graph = {
    "A":[{"to":"B","travel_time":2,"is_express":"False","line":"1호선"}],
    "B":[{"to":"A","travel_time":2,"is_express":"False","line":"1호선"},
         {"to":"C","travel_time":2,"is_express":"False","line":"1호선"},
         {"to":"D","travel_time":3,"is_express":"True","line":"1호선"}],
    "C":[{"to":"D","travel_time":2,"is_express":"False","line":"1호선"}],
    "D":[{"to":"B","travel_time":3,"is_express":"True","line":"1호선"},
         {"to":"E","travel_time":2,"is_express":"False","line":"1호선"},
         {"to":"I","travel_time":2,"is_express":"False","line":"2호선"},
         {"to":"H","travel_time":2,"is_express":"False","line":"2호선"}],
    "E":[{"to":"D","travel_time":2,"is_express":"False","line":"1호선"},
         {"to":"F","travel_time":2,"is_express":"False","line":"1호선"}],
    "F":[{"to":"E","travel_time":2,"is_express":"False","line":"1호선"}],
    "I":[{"to":"D","travel_time":2,"is_express":"False","line":"1호선"},
         {"to":"J","travel_time":2,"is_express":"False","line":"2호선"}],
    "J":[{"to":"I","travel_time":2,"is_express":"False","line":"2호선"}],
    "H":[{"to":"D","travel_time":2,"is_express":"False","line":"1호선"},
         {"to":"G","travel_time":2,"is_express":"False","line":"2호선"}],
    "G":[{"to":"H","travel_time":2,"is_express":"False","line":"2호선"}]
}
#환승에 대한 travel_time를 생각해봐야함 (환승이 이점이 되면 안되고 벌점이 되어야함)

import heapq

def dijkstra(graph,start):
    #1. 거리 테이블 초기화
    INF = (10**9,10**9)
    dist = {node: INF for node in graph}
    dist[start] = (0,0)


    #2. 우선순위 큐 (거리,노드)
    pq = []
    heapq.heappush(pq,((0,0),start,None))
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
        (cur_transfer,cur_dist), cur_node,prev_line = heapq.heappop(pq)

        #이미 더 짧은 경로가 있으면 스킵
        if (cur_transfer,cur_dist) > dist[cur_node]:
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
            travel_time = edge["travel_time"]
            train_is_express = edge["is_express"]
            next_line = edge["line"]
            add_transfer = 0
            new_dist = cur_dist + travel_time

            if prev_line is not None and prev_line != next_line:
                add_transfer = 1
            new_transfer = cur_transfer + add_transfer
            new_cost = (new_transfer, new_dist)
            # 더 짧은 경로 발견 시 갱신

            if new_cost < dist[next_node]:
                dist[next_node] = new_cost
                prev[next_node] = cur_node
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
        #출발역에서 도착할때까지 반복
        path.append(cur)
        #현재 노드를 경로에 추가
        cur = prev[cur]
        #최단 경로일때 뒤로 한칸 이동 ("D"였을 경우 "B"로 이동)
        #만약 cur == "D"/ prev["D"] = "B" -> cur = "B"

    path.append(start)
    path.reverse()
    return path

start = input("출발 지점을 입력하세요 : ")
end = input("도착지점을 입력하세요 : ")

dist, prev = dijkstra(graph, start)
path = get_path(prev,start, end)

print("최단거리:",dist[end][1])
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



