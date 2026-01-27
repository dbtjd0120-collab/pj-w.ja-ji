import os
import pandas as pd


current_file = os.path.abspath(__file__)
backend_file = os.path.dirname(current_file)
project_file = os.path.dirname(backend_file)

Timetable_path = os.path.join(project_file,"data","raw","timetable_sample.csv")
Transfer_path = os.path.join(project_file,"data","processed","transfer_list.json")
df = pd.read_csv(Timetable_path,encoding = "euc-kr")
print(df.head())


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

for train_id, group in df.groupby("열차코드"):

    group = group.sort_values("열차출발시간")

    rows = group.to_dict("records")

    for i in range(len(rows) - 1):
        cur = rows[i]
        nxt = rows[i+1]

        from_node = cur["역사코드"]
        to_node = nxt["역사코드"]

        dep_time = time_to_second(cur["열차출발시간"])
        arr_time = time_to_second(nxt["열차도착시간"])

        if dep_time is None or arr_time is None:
            continue

        travel_time = arr_time - dep_time

        edge = {
            "to": to_node,
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





