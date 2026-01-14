import time
import pandas as pd
import json
import os

# 파일 경로 설정
# 1. 이 파일(preprocessing_v2.py)의 절대 경로를 계산합니다.
# d:\...\backend\preprocessing_v2.py
current_file = os.path.abspath(__file__)

# 2. 이 파일이 들어있는 폴더(backend) 경로를 찾습니다.
# d:\...\backend
backend_dir = os.path.dirname(current_file)

# 3. 한 단계 위로 올라가서 프로젝트 루트(P1.Optimizing_Subway_Travel)를 찾습니다.
# d:\...\P1.Optimizing_Subway_Travel
project_root = os.path.dirname(backend_dir)

# 4. 이제 어떤 환경에서도 에러가 나지 않는 절대 경로를 완성합니다.
TIMETABLE_PATH = os.path.join(project_root, 'data', 'raw', 'timetable.csv')
TRANSFER_PATH = os.path.join(project_root, 'data', 'raw', 'transfer_info.csv')
OUTPUT_DIR = os.path.join(project_root, 'data', 'processed', '')

# 확인용 출력 (에러 나면 이 경로가 맞는지 눈으로 확인 가능합니다)
print(f"--- 경로 설정 확인 ---")
print(f"루트 경로: {project_root}")
print(f"불러올 파일: {TIMETABLE_PATH}")
print(f"----------------------")

def time_str_to_seconds(t_str):
    """ HH:MM:SS 또는 MM:SS 형태의 시간을 초(int)로 변환 """
    if pd.isna(t_str): return None
    # isna() -> 해당 데이터가 결측치(Missing Value : Nan, None, null같은 것들)인지 확인
    # 열차의 첫 역 도착시간 같은 결측치라면 None 반환
    # 0이 유효한 값일 수 있으니 0으로 반환하면 안 됨
    try:
        parts = list(map(int, t_str.split(':')))
        # HH:MM:SS 또는 MM:SS 형태로 정수 list 생성 (길이는 알아서)
        if len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:  # MM:SS (환승 소요시간용)
            return parts[0] * 60 + parts[1]
        return 0
    except:
        return 0

def preprocess_all():
    # 1. 데이터 로딩
    print("데이터 로딩 중...")
    # try:
        # 인코딩은 데이터 환경에 따라 cp949 또는 EUC-KR 선택
    df = pd.read_csv(TIMETABLE_PATH, encoding='EUC-KR', dtype={'역사코드': str, '호선': str, '열차코드': str})
    df_trans = pd.read_csv(TRANSFER_PATH, encoding='EUC-KR', dtype={'호선': str})
        # df = pandas의 DataFrame 객체
        # pandas의 read_csv는 기본적으로 숫자형 데이터를 숫자로 읽음
        # 문자열로 지정되어야 하는 데이터가 숫자로 변환되는 것을 방지하기 위해 dtype 지정
        # 나중에 "수인분당" 같은 호선명이 숫자로 바뀌는 문제 방지하기 위함.
    # except:
    #     df = pd.read_csv(TIMETABLE_PATH, encoding='cp949', dtype={'역사코드': str, '호선': str})
    #     df_trans = pd.read_csv(TRANSFER_PATH, encoding='cp949', dtype={'호선': str})

    # --- PART A: 열차 시간표 그래프 생성 ---
    
    # 2. 시간 변환 및 정렬
    df['arr_sec'] = df['열차도착시간'].apply(time_str_to_seconds)
    df['dept_sec'] = df['열차출발시간'].apply(time_str_to_seconds)
    df['arr_sec'] = df['arr_sec'].fillna(df['dept_sec'])
    df['dept_sec'] = df['dept_sec'].fillna(0)

    # 결국 출발시간 이전에만 도착하면 되니까 결측치는 0이 아닌 출발시간으로 대체
    # .fillna() : fill+na(Not Available) -> 결측치(NaN)를 채운다는 의미
    df = df.sort_values(by=['주중주말', '열차코드', 'arr_sec'])
    # 주중주말, 열차코드 순으로 정렬하고, 시간순으로도 정렬하면 유효한 간선(edge)데이터 추출 가능

    # 3. 다음 역 정보 연결 (Pandas의 Shift 사용 - for문 보다 훨씬 빠름)
    # 다음 행의 정보를 현재 행의 'next_' 컬럼(옆칸)으로 가져옴
    df['next_station_code'] = df['역사코드'].shift(-1)
    df['next_station_name'] = df['역사명'].shift(-1)
    df['next_line'] = df['호선'].shift(-1)           # 다음줄 호선이 동일한지 확인
    df['next_arr_sec'] = df['arr_sec'].shift(-1)
    df['next_train_code'] = df['열차코드'].shift(-1)
    
    # 4. 동일 열차인 간선(edge)만 추출
    # 현재 행의 열차코드와 다음 행의 열차코드를 비교하여 같을 때만 유효한 간선으로 간주
    # df['열차코드'] -> df의 열차코드 시리즈(세로줄 전체, 리스트 덩어리)
    # df[조건] -> 시리즈를 비교해보며 조건에 맞는 행들만 필터링
    # .copy() -> 원본df를 보존한 상태로 조건에 맞는 복사본 생성
    # .copy()를 하지 않으면 원본의 일부를 참조하는 뷰(View)가 되어 이후 연산에서 SettingWithCopyWarning 경고 발생
    valid_edges = df[
        (df['열차코드'] == df['next_train_code']) and 
        (df['호선'] == df['next_line']) and
        (df['역사코드'] != df['next_station_code'])
    ].copy()
    valid_edges['travel_time'] = valid_edges['next_arr_sec'] - valid_edges['dept_sec']

    # 5. 요일별 그래프 저장
    day_types = {'DAY': 'weekday', 'SAT': 'saturday', 'END': 'holiday'}
    # OUTPUT_DIR 경로가 없으면 폴더 생성
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    for raw_day, file_suffix in day_types.items():  # file_suffix(파일 접미사) -> 저장할 파일명에 들어갈 요일 구분자
        day_df = valid_edges[valid_edges['주중주말'] == raw_day]    # 특정 날 데이터만 필터링
        graph = {}  # 빈 딕셔너리 생성, hash map 구조로 그래프 표현
        
        for station_code, group in day_df.groupby('역사코드'):
            # groupby() -> 특정 컬럼을 기준으로 DataFrame을 그룹화
            graph[station_code] = []    # 특정 역에 대한 처리 중...
            # group은 해당 역에 속한 모든 행(데이터)들의 DataFrame
            # iterrows() -> DataFrame의 각 행을 순회하며 (인덱스, 행 데이터) 튜플 반환
            for _, row in group.iterrows():     # _ -> 해당 인덱스는 사용하지 않으므로 무시
                graph[station_code].append({
                    "dest_code": row['next_station_code'],  # 다음 역 코드
                    "dest_name": row['next_station_name'],  # 다음 역 이름
                    "line": row['호선'],
                    "train_code": row['열차코드'],
                    "dept_time": row['dept_sec'],           # 현재 역 출발 시간 (초)
                    "arr_time": row['next_arr_sec'],        # 다음 역 도착 시간 (초)
                    "express": row['급행여부']  ,           # 급행 여부
                })
            graph[station_code].sort(key=lambda x: x['dept_time']) # 시간순 정렬 (이진 탐색 알고리즘 사용 위함)
            # .sort(key) -> key 기준으로 리스트 정렬
            # key= -> 정렬 기준 지정. 함수로 집어넣어야 함.
            # lambda x : -> x를 결과값으로 주는 익명함수
            # graph = {특정 역사코드 : {"dest_code": "0151", "dest_name": "시청", "dept_time": 32400, "line": "1", ... }}, ... 의 형식인데
            # sort 함수가 정렬하려고 꺼낸 {"dest_code": "0151", "dest_name": "시청", ...} 부분을 x라고 받기로 한 거임.
            # station_code를 key값으로 가지는 value를 x로 받는데, 그 x는 또 여러 개의 딕셔너리 형태인것임.
            # x['dept_time'] -> 해당 딕셔너리 x에서 출발 시간에 해당하는 값 반환

            # # lambda를 안쓰려면 함수를 한 번만 쓰더라도 따로 정의하고 사용해야 함
            # def get_time(x):
            #     return x['dept_time']
            # graph[station_code].sort(key=get_time)

        with open(f"{OUTPUT_DIR}graph_{file_suffix}.json", 'w', encoding='EUC-KR') as f:
            json.dump(graph, f, ensure_ascii=False)
            # with...as f : -> 자원 획득/사용/반납 시에 사용, 이 블록이 끝나면 자동으로 f.close() 호출
            # open(파일경로, 모드, 인코딩) -> 파일 열기
            # 'w' -> 쓰기 모드 (파일이 없으면 새로 생성, 있으면 덮어씀)
            # json.dump() -> 파이썬 디셔너리를 JSON 형태의 텍스트로 바꿔서 파일에 저장
            # f -> with문에서 만든 파일 구멍
            # ensure_ascii=False -> 한글이 깨지지 않도록 설정
            print(f" -> graph_{file_suffix}.json 저장 완료")

    # --- PART B: 환승 소요 시간 데이터 처리 ---

    # 6. 환승 정보 구조화
    print("환승 데이터 처리 중...")
    transfer_dict = {}
    
    # [추가] 역사명 -> 역사코드 매핑 딕셔너리 생성 (시간표에 존재하는 역만 환승 가능하게 함)
    # df는 위에서 로드한 시간표 데이터입니다.
    name_to_code = df.set_index('역사명')['역사코드'].to_dict()
    # [추가] 시간표에 존재하는 실제 노선 목록 (필터링용)
    valid_lines = set(df['호선'].unique())

    for _, row in df_trans.iterrows():
        st_name = row['환승역명']
        st_code = name_to_code.get(st_name) 
            
        # 2. 코드가 정상적으로 존재할 때만 바구니 작업을 시작합니다.
        if st_code: 
            # '4호선' 또는 '4' 형태를 통일하기 위해 '호선' 글자를 빈칸으로 대체
            # .strip() -> 문자열 앞뒤의 불필요한 공백 제거
            from_line = str(row['호선']).replace('호선', '').strip()
            to_line = str(row['환승노선']).replace('호선', '').strip()
            
            if to_line in valid_lines:
                # [바구니 확인 및 생성]
                # 해당 딕셔너리의 키 목록에 st_code가 없으면 새로 생성
                if st_code not in transfer_dict:
                    transfer_dict[st_code] = {}
                
                # 데이터 저장
                walk_sec = time_str_to_seconds(row['환승소요시간'])
                walk_distance = int(row.get('환승거리', 0))
                transfer_dict[st_code][f"{from_line}:{to_line}"] = {
                    "walk_sec": walk_sec,
                    "walk_distance": walk_distance
                    # [데이터 구조 예시]
                    # {
                    #   "0150": {                 # [st_code] : 서울역 서랍을 연다
                    #     "1:4": {                # [f"{from_line}:{to_line}"] : 그중 1호선→4호선 칸을 본다
                    #       "walk_sec": 300,      # 실제 값 1
                    #       "walk_distance": 250  # 실제 값 2
                    #     },
                    #     "1:A": {                # 공항철도 환승 정보 등 다른 칸도 있을 수 있음
                    #       "walk_sec": 600,
                    #       "walk_distance": 500
                    #     }
                    #   }
                    # }
                }

    # 저장 (indent=2를 주어 가독성 확보)
    with open(f"{OUTPUT_DIR}transfer_list.json", 'w', encoding='EUC-KR') as f:
        json.dump(transfer_dict, f, ensure_ascii=False, indent=2)
    print(" -> transfer_list.json 저장 완료 (역사코드 기반 필터링 적용)")

    # 7. 역 목록(Station List) 저장
    # 유저가 역 이름으로 검색하면 해당 역의 '역사코드'를 찾기 위한 용도
    unique_stations = df[['역사코드', '역사명', '호선']].drop_duplicates().to_dict(orient='records')
    with open(f"{OUTPUT_DIR}stations_list.json", 'w', encoding='EUC-KR') as f:
        json.dump(unique_stations, f, ensure_ascii=False)
    print(" -> stations_list.json 저장 완료")

if __name__ == "__main__":
    start_time = time.time()
    preprocess_all()
    elapsed_time = time.time() - start_time
    print("-" * 40)
    print("전체 전처리 프로세스가 성공적으로 완료되었습니다.")
    print(f"⏱️ 총 소요 시간: {elapsed_time:.2f}초")
    # 17.28초
    print("-" * 40)