
import os
import json
from datetime import datetime

# --- 경로 설정 ---
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(current_file)
project_root = os.path.dirname(backend_dir)
DATA_DIR = os.path.join(project_root, 'data', 'processed')

class SubwayPathfinder:
    def __init__(self):
        """
        함수 정의 앞에 붙은 _ 두개는 name mangling(이름변경). 규칙에 따라 외부에서 접근 불가
        같은 클래스의 다른 함수를 사용할 것이라 self를 인자로 정의함
        """
        self.day_type = self._get_today_type()
        self._load_data()
        self._build_indices()
        self.count = 0
        # print(f"[{self.day_type}] 데이터 로딩 완료. 탐색 준비가 되었습니다.")

    def _get_today_type(self):  # 날짜를 요일로
        """함수 정의 앞에 붙은 _ 하나는 내부용(private) 메서드임을 나타냄"""
        weekday = datetime.now().weekday()
        day_dict = {5: 'saturday', 6: 'holiday'}

        """day_dict에 없으면(0~4) 'weekday'를 반환"""
        return day_dict.get(weekday, 'weekday')      # .get() -> 마우스 올려서 설명 확인

    def _load_data(self):       # 데이터 로드
        try:
            with open(os.path.join(DATA_DIR, f'graph_{self.day_type}.json'), 'r', encoding='EUC-KR') as f:
                self.graph = json.load(f)
            with open(os.path.join(DATA_DIR, 'transfer_list.json'), 'r', encoding='EUC-KR') as f:
                self.transfer_list = json.load(f)
            with open(os.path.join(DATA_DIR, 'stations_list.json'), 'r', encoding='EUC-KR') as f:
                self.stations_raw = json.load(f)
        except Exception as e:
            print(f"❌ 로딩 실패. (오류 코드: {e})")
            exit()

    def _build_indices(self):
        self.code_to_info = {}      # 역사코드 -> {역사정보 딕셔너리}
        self.name_to_code = {}      # 역사명 -> [역사코드1, 역사코드2, ...], 출발지 선정에 사용
        self.station_group = {}     # 역사명 -> {호선: 역사코드, ...} (환승용), 환승 시 특정 호선의 코드 찾기 위해 사용
        for st in self.stations_raw:
            st_code, st_name, line = st['역사코드'], st['역사명'], st['호선']
            self.code_to_info[st_code] = st
            self.name_to_code.setdefault(st_name, []).append(st_code)
            self.station_group.setdefault(st_name, {})[line] = st_code
        """
        .setdefault(key, default) -> key가 없으면 default(빈 list[]/빈 dict{})로 초기화하고, 있으면 value(list/dict) 반환
        파이썬에서 list는 배열이 아니라 객체이므로 .append() 메서드를 사용하여 list에 요소 추가 가능
        self.station_group의 key는 역사명, value는 {호선: 역사코드} 딕셔너리가 됨
        code_to_info, name_to_code를 station_group으로 통합하여 사용하면 매번 .values()를 사용해 리스트로 변환해야 함 -> 비효율적?
        """

    def test_movetime_check(self):
        # 최대 역간 이동시간 확인
        mtime_max=0
        for stcode, value in self.graph.items():
            for tvalue in value:
                mtime = tvalue['arr_time'] - tvalue['dept_time']
                if mtime > mtime_max and mtime > 0:
                    mtime_max = mtime
                    print(
                        f"최대 이동시간 갱신: {mtime_max}초 "
                        f"({stcode} → {tvalue['dest_code']} ({tvalue['dest_name']}에 {tvalue['arr_time']}), "
                        f"{tvalue['line']}호선, "
                        f"열차 {tvalue['train_code']})"
                    )

    def test_movetime_check_same(self):
        # 역간 이동 거리가 전부 같은지 확인    
        # 1. 모든 구간의 소요 시간을 저장 (key: (출발, 도착), value: 소요시간)
        # 열차가 여러 대이므로 첫 번째 열차의 소요시간만 대표로 기록합니다.
        section_times = {}
        for start_code, trains in self.graph.items():
            for edge in trains:
                dest_code = edge['dest_code']
                duration = edge['arr_time'] - edge['dept_time']
                # 같은 구간의 여러 열차 중 첫 번째 것만 기록 (이미 정렬되어 있음)
                cur_key = (dest_code, start_code)
                if cur_key not in section_times:
                    section_times[cur_key] = set()
                section_times[cur_key].add(duration)
                # 조건에 맞으면 {(목적지, 출발지):(이동시간 set)}으로 딕셔너리들 구성.

        checked = set()    
        
        for (start, dest), durations in section_times.items():
            mirror_key = (dest, start)
            if mirror_key in section_times and (dest, start) not in checked:
                if durations != section_times[mirror_key]:                
                    start_name = self.code_to_info[start]['역사명']
                    dest_name = self.code_to_info[dest]['역사명']
                    
                    print(f"[시간 불일치] {start_name}({start}) ↔ {dest_name}({start})")
                    print(f"   - {start}->{dest}: {sorted(list(durations))}초")
                    print(f"   - {dest}->{start}: {sorted(list(section_times[mirror_key]))}초")
                checked.add((start, dest))
                checked.add((dest, start))



if __name__ == "__main__":
    test = SubwayPathfinder()
    test.test_movetime_check()
    test.test_movetime_check_same()





    """
    .setdefault(key, default) -> key가 없으면 default(빈 list[]/빈 dict{})로 초기화하고, 있으면 value(list/dict) 반환
    파이썬에서 list는 배열이 아니라 객체이므로 .append() 메서드를 사용하여 list에 요소 추가 가능
    self.station_group의 key는 역사명, value는 {호선: 역사코드} 딕셔너리가 됨
    code_to_info, name_to_code를 station_group으로 통합하여 사용하면 매번 .values()를 사용해 리스트로 변환해야 함 -> 비효율적?
    """