import time
import pandas as pd
import json
import os

current_file = os.path.abspath(__file__)        # 파일 절대경로 계산
backend_dir = os.path.dirname(current_file)     # 상위폴더로 이동
project_root = os.path.dirname(backend_dir)     # 상취 폴더로 이동

TIMETABLE_PATH = os.path.join(project_root, 'data', 'raw', 'timetable.csv')
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
    df = pd.read_csv(TIMETABLE_PATH, encoding='EUC-KR', dtype={'호선': str, '열차코드': str})
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

    valid_edges['역사코드'] = valid_edges['역사코드'].astype(str)


    day_types = {'DAY': 'weekday', 'SAT': 'saturday', 'END': 'holiday'}
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

    for day_type, file_suffix in day_types.items():
        day_df = valid_edges[valid_edges['주중주말'] == day_type]
        graph = {}
        for station_code, group in day_df.groupby('역사코드'):
            graph[station_code] = {}
            for dest_code, dest_group in group.groupby('next_station_code'):
                graph[station_code][dest_code] = []
                for _, row in dest_group.iterrows():
                    graph[station_code][dest_code].append({
                        "line": str(row['호선']),
                        "dep_time": int(row['dep_sec']),
                        "arr_time": int(row['next_arr_sec']),
                        "express": int(row['급행여부'])
                    })
                graph[station_code][dest_code].sort(key=lambda x: x['dep_time'])

        with open(f"{OUTPUT_DIR}graph_{file_suffix}.json", 'w', encoding='EUC-KR') as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)
            print(f" -> graph_{file_suffix}.json 저장 완료")

    print("환승 데이터 처리 중...")
    transfer_dict = {}

    # {현재역코드 : {trs역코드1:환승정보, trs역코드2:환승정보}} 형태로 저장
    name_to_code = df.groupby(['역사명', '호선'])['역사코드'].first().to_dict()
    line_set = set(df['호선'].unique())

    for _, row in df_trans.iterrows():
        st_name = row['환승역명']
        from_line = row['호선']
        to_line = row['환승노선'].replace('호선', '')
        # 데이터 타입이 무엇이든 안전하게 처리하려면 자료형 변환을 해줘야 한다.
        # to_line = str(row['환승노선']).replace('호선', '').strip()
            
        if to_line in line_set and from_line in line_set:
            st1_code = name_to_code.get((st_name, from_line))
            st2_code = name_to_code.get((st_name, to_line))

            if st1_code is not None and st2_code is not None:
                walk_sec = time_str_to_seconds(row['환승소요시간'])
                walk_distance = int(row.get('환승거리'))

                if st1_code not in transfer_dict: transfer_dict[st1_code] = {}
                else:
                    transfer_dict[st1_code][st2_code] = {
                    "walk_sec": walk_sec,
                    "walk_distance": walk_distance
                }
                if st2_code not in transfer_dict: transfer_dict[st2_code] = {}
                else:
                    transfer_dict[st2_code][st1_code] = {
                        "walk_sec": walk_sec,
                        "walk_distance": walk_distance
                    }

    with open(f"{OUTPUT_DIR}transfer_list.json", 'w', encoding='EUC-KR') as f:
        json.dump(transfer_dict, f, ensure_ascii=False, indent=2)
    print(" -> transfer_list.json 저장 완료")

    # 역 목록(Station List) 저장
    station_map = df.groupby('역사명')['역사코드'].apply(lambda x: list(set(x))).to_dict()
    with open(f"{OUTPUT_DIR}stations_list.json", 'w', encoding='EUC-KR') as f:
        json.dump(station_map, f, ensure_ascii=False, indent=2)
    print(" -> stations_list.json 저장 완료")


if __name__ == "__main__":
    start_time = time.time()
    preprocess_all()
    elapsed_time = time.time() - start_time
    print("-" * 40)
    print("전처리 프로세스 완료")
    print(f"총 소요 시간: {elapsed_time:.2f}초")
    print("-" * 40)