import time
import pandas as pd
import json
import os

current_file = os.path.abspath(__file__)        # 파일 절대경로 계산
backend_dir = os.path.dirname(current_file)     # 상위폴더로 이동
project_root = os.path.dirname(backend_dir)     # 상취 폴더로 이동

TIMETABLE_PATH = os.path.join(project_root, 'data', 'raw', 'timetable_sample.csv')
TRANSFER_PATH = os.path.join(project_root, 'data', 'raw', 'transfer_info.csv')
OUTPUT_DIR = os.path.join(project_root, 'data', 'processed', '')

print(f"--- 경로 설정 확인 ---")
print(f"루트 경로: {project_root}")
print(f"불러올 파일: {TIMETABLE_PATH}")
print(f"----------------------")

def time_str_to_seconds(t_str):
    if pd.isna(t_str): return None
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
    df = pd.read_csv(TIMETABLE_PATH, encoding='EUC-KR', dtype={'역사코드': str, '호선': str, '열차코드': str})
    df_trans = pd.read_csv(TRANSFER_PATH, encoding='EUC-KR', dtype={'호선': str})

    df['arr_sec'] = df['열차도착시간'].apply(time_str_to_seconds)
    df['dep_sec'] = df['열차출발시간'].apply(time_str_to_seconds)
    df.loc[df['arr_sec'] <= 0, 'arr_sec'] = None
    df.loc[df['dep_sec'] <= 0, 'dep_sec'] = None
    df['arr_sec'] = df['arr_sec'].fillna(df['dep_sec'])
    df['dep_sec'] = df['dep_sec'].fillna(df['arr_sec'])

    df = df.sort_values(by=['주중주말', '열차코드', 'arr_sec'])

    # .shift(n) -> n만큼 행을 아래로 내림
    prev_train = df['열차코드'].shift(1)
    next_train = df['열차코드'].shift(-1)

    # 출발역과 도착역은 False, 중간역은 True인 series 생성
    mid_st = (df['열차코드'] == prev_train) & (df['열차코드'] == next_train)
    # 중간역이고 출발시간 도착시간이 같은 역은 True인 series 생성
    drop_st = (df['arr_sec'] == df['dep_sec']) & mid_st
    # 버릴 대상을 제외한 역을 살린다.
    df = df[~drop_st]

    df['next_train_code'] = df['열차코드'].shift(-1)
    df['next_line'] = df['호선'].shift(-1)
    df['next_station_code'] = df['역사코드'].shift(-1)
    df['next_arr_sec'] = df['arr_sec'].shift(-1)

    valid_edges = df[
        (df['열차코드'] == df['next_train_code']) &
        (df['호선'] == df['next_line'])
    ].copy()

    day_types = {'DAY': 'weekday', 'SAT': 'saturday', 'END': 'holiday'}
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    for day_type, file_suffix in day_types.items():
        day_df = valid_edges[valid_edges['주중주말'] == day_type]
        graph = {}
        for station_code, group in day_df.groupby('역사코드'):
            # groupby() -> 특정 컬럼을 기준으로 DataFrame을 그룹화
            graph[station_code] = []
            for _, row in group.iterrows():     # _ -> 해당 인덱스는 사용하지 않으므로 무시
                graph[station_code].append({
                    "dest_code": row['next_station_code'],  # 다음 역 코드
                    "line": row['호선'],
                    "dep_time": row['dep_sec'],           # 현재 역 출발 시간 (초)
                    "arr_time": row['next_arr_sec'],        # 다음 역 도착 시간 (초)
                    "express": row['급행여부']  ,            # 급행 여부
                })
            graph[station_code].sort(key=lambda x: x['dep_time']) # 시간순 정렬 (이진 탐색 알고리즘 사용 위함)

        with open(f"{OUTPUT_DIR}graph_{file_suffix}.json", 'w', encoding='EUC-KR') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
            print(f" -> graph_{file_suffix}.json 저장 완료")

    print("환승 데이터 처리 중...")
    transfer_dict = {}
    
    # {역사명 :역사코드} 형태로 저장
    name_to_code = df.groupby(['역사명', '호선'])['역사코드'].first().to_dict()

    for _, row in df_trans.iterrows():
        st_name = row['환승역명']
        from_line = row['호선']
        to_line = row['환승노선'].replace('호선', '')
        st1_code = name_to_code.get((st_name, from_line))
        st2_code = name_to_code.get((st_name, to_line))

        if st1_code and st2_code:
            walk_sec = time_str_to_seconds(row['환승소요시간'])
            walk_distance = int(row.get('환승거리', 0))

            if st1_code not in transfer_dict: transfer_dict[st1_code] = {}
            transfer_dict[st1_code][st2_code] = {
                "walk_sec": walk_sec,
                "walk_distance": walk_distance
            }
            if st2_code not in transfer_dict: transfer_dict[st2_code] = {}
            transfer_dict[st2_code][st1_code] = {
                "walk_sec": walk_sec,
                "walk_distance": walk_distance
            }

    with open(f"{OUTPUT_DIR}transfer_list.json", 'w', encoding='EUC-KR') as f:
        json.dump(transfer_dict, f, ensure_ascii=False, indent=2)
    print(" -> transfer_list.json 저장 완료 (역사코드 기반 필터링 적용)")

    # 역 목록(Station List) 저장
    unique_stations = df[['역사코드', '역사명', '호선']].drop_duplicates().to_dict(orient='records')
    with open(f"{OUTPUT_DIR}stations_list.json", 'w', encoding='EUC-KR') as f:
        json.dump(unique_stations, f, ensure_ascii=False, indent=2)
    print(" -> stations_list.json 저장 완료")


if __name__ == "__main__":
    start_time = time.time()
    preprocess_all()
    elapsed_time = time.time() - start_time
    print("-" * 40)
    print("전처리 프로세스 완료")
    print(f"총 소요 시간: {elapsed_time:.2f}초")
    print("-" * 40)