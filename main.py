# =====================================================================
#  Mini NPU Simulator : 그림이 십자가(Cross)인지 X인지 MAC 연산으로 판별
# =====================================================================
#
#  [번호 읽는 법]
#   - 실행 순서 : ①, ②, ③ ... (프로그램이 실제로 지나가는 순서)
#   - 함수 이름표 : [F1], [F2] ... (각 함수 위에 붙어 있음)
#     실행 순서 주석에 "→ [F2]"라고 적혀 있으면 그 함수로 이동했다는 뜻
#
#  [전체 실행 흐름 지도]
#   ① 맨 아래 main() 호출로 시작 → [F15] main
#   ② 모드 선택
#      ├─ "1" → ③ [F12] user_mode (사용자 입력 모드)
#      │     ③-1 입력 방식 선택
#      │     ③-2 직접 입력  → [F11] input_grid
#      │     ③-2 자동 생성  → [F5] make_cross, [F6] make_x, [F9] print_grid
#      │     ③-3 점수 계산  → [F2] mac
#      │     ③-4 시간 측정  → [F4] measure_ms → [F2] mac
#      │     ③-5 판정       → [F3] judge
#      │     ③-6 성능 표    → [F10] print_performance
#      │
#      └─ 그 외 → ④ [F14] json_mode (data.json 분석 모드)
#            ④-1 data.json 파일 읽기
#            ④-2 필터 로드  → [F1] normalize
#            ④-3 패턴마다 검사·판정 → [F13] check_case
#                   → [F7] is_size, [F1] normalize, [F2] mac, [F3] judge
#            ④-4 성능 표    → [F10] print_performance
#            ④-5 결과 요약 (총/통과/실패)
# =====================================================================

import json   # data.json 파일을 읽기 위한 기본 도구
import time   # 시간 측정을 위한 기본 도구

EPSILON = 1e-9   # 두 점수 차이가 이보다 작으면 "같은 점수(동점)"로 본다
REPEAT = 10      # 시간 측정 반복 횟수

# 라벨 정규화 표: data.json의 제각각인 표기를 표준 라벨(Cross / X)로 통일
LABELS = {"+": "Cross", "cross": "Cross", "x": "X"}


# [F1] 라벨 정규화: '+', 'cross', 'x' → 'Cross' 또는 'X'
#      사용처: ④-2 필터 로드, [F13] check_case
def normalize(label):
    return LABELS.get(str(label).lower())


# [F2] MAC 연산: 같은 위치 숫자끼리 곱해서(Multiply) 전부 더한다(Accumulate)
#      사용처: ③-3, [F4] measure_ms, [F13] check_case
def mac(pattern, filter_grid):
    n = len(pattern)
    total = 0.0
    for i in range(n):              # i = 행(가로줄) 번호
        for j in range(n):          # j = 열(세로줄) 번호
            total += pattern[i][j] * filter_grid[i][j]
    return total


# [F3] 판정: 두 점수 중 높은 쪽의 이름을 돌려준다
#      차이가 EPSILON보다 작으면 소수 오차일 수 있으므로 "UNDECIDED"(판정 불가)
#      사용처: ③-5, [F13] check_case
def judge(score_a, score_b, name_a, name_b):
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    if score_a > score_b:
        return name_a
    return name_b


# [F4] 시간 측정: MAC 계산만 REPEAT(10)번 실행해 1회 평균 시간(ms)을 돌려준다
#      사용처: ③-4, [F10] print_performance
def measure_ms(pattern, filter_grid):
    start = time.perf_counter()
    for _ in range(REPEAT):
        mac(pattern, filter_grid)                   # → [F2]
    return (time.perf_counter() - start) / REPEAT * 1000   # 초 → ms 변환


# [F5] 패턴 생성기(보너스) - 십자가: 가운데 가로줄 또는 가운데 세로줄이면 1
#      사용처: ③-2 자동 생성, [F10] print_performance
def make_cross(n):
    c = n // 2                      # 가운데 줄 번호
    grid = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == c or j == c:
                row.append(1)
            else:
                row.append(0)
        grid.append(row)
    return grid


# [F6] 패턴 생성기(보너스) - X: 두 대각선(↘ i==j, ↙ i+j==n-1) 위면 1
#      사용처: ③-2 자동 생성, [F10] print_performance
def make_x(n):
    grid = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j or i + j == n - 1:
                row.append(1)
            else:
                row.append(0)
        grid.append(row)
    return grid


# [F7] 크기 검사: 표가 정확히 N×N인지 확인 (행 개수, 각 행의 열 개수)
#      사용처: [F13] check_case
def is_size(grid, n):
    if len(grid) != n:
        return False
    for row in grid:
        if len(row) != n:
            return False
    return True


# [F8] 화면에 구역 제목 출력
def print_title(title):
    print("\n#" + "-" * 40)
    print("# " + title)
    print("#" + "-" * 40)


# [F9] 표(그림)를 화면에 출력
#      사용처: ③-2 자동 생성
def print_grid(name, grid):
    print(name)
    for row in grid:
        print(" ".join(str(v) for v in row))
    print()


# [F10] 성능 표 출력: 크기별로 [F5][F6]로 그림을 만들고 [F4]로 시간을 잰다
#       사용처: ③-6, ④-4
def print_performance(sizes):
    print_title(f"성능 분석 (평균/{REPEAT}회)")
    print(f"{'크기':<10}{'평균 시간(ms)':>16}{'연산 횟수(N²)':>16}")
    print("-" * 44)
    for n in sizes:
        ms = measure_ms(make_cross(n), make_x(n))   # → [F5], [F6], [F4]
        print(f"{f'{n}×{n}':<10}{ms:>16.4f}{n * n:>16}")


# [F11] 키보드로 N줄 입력받아 표로 만든다
#       숫자 개수가 틀리거나 숫자가 아니면 안내 후 처음부터 다시 입력받는다
#       사용처: ③-2 직접 입력
def input_grid(name, n=3):
    while True:
        print(f"{name} ({n}줄 입력, 공백 구분)")
        try:
            grid = []
            for _ in range(n):
                row = [float(v) for v in input().split()]   # 숫자가 아니면 ValueError
                if len(row) != n:
                    raise ValueError                        # 개수가 틀려도 ValueError
                grid.append(row)
            return grid
        except ValueError:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.\n")


# [F12] ③ 모드 1: 사용자 입력 모드
def user_mode():
    # ③-1 입력 방식 선택
    print("\n1. 직접 입력 (3x3)")
    print("2. 패턴 생성기로 자동 생성 (N×N)")

    if input("선택: ").strip() == "1":
        # ③-2 직접 입력: 필터 A, B → 저장 확인 → 패턴
        n = 3
        print_title("[1] 필터 입력")
        filter_a = input_grid("필터 A")                   # → [F11]
        filter_b = input_grid("필터 B")                   # → [F11]
        print("✓ 필터 A, B 저장 완료")
        print_title("[2] 패턴 입력")
        pattern = input_grid("패턴")                      # → [F11]
    else:
        # ③-2 자동 생성(보너스): 크기 N → 필터 A=십자가, B=X → 패턴 선택
        print_title("[1] 필터 자동 생성")
        n = int(input("크기 N 입력: "))
        filter_a = make_cross(n)                          # → [F5]
        filter_b = make_x(n)                              # → [F6]
        print_grid("필터 A (Cross)", filter_a)            # → [F9]
        print_grid("필터 B (X)", filter_b)                # → [F9]
        print("✓ 필터 A, B 저장 완료")
        print_title("[2] 패턴 자동 생성")
        print("1. Cross 패턴")
        print("2. X 패턴")
        if input("선택: ").strip() == "1":
            pattern = make_cross(n)                       # → [F5]
        else:
            pattern = make_x(n)                           # → [F6]
        print_grid("패턴", pattern)                       # → [F9]

    # ③-3 점수 계산
    print_title("[3] MAC 결과")
    score_a = mac(pattern, filter_a)                      # → [F2]
    score_b = mac(pattern, filter_b)                      # → [F2]
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")

    # ③-4 시간 측정
    print(f"연산 시간(평균/{REPEAT}회): {measure_ms(pattern, filter_a):.4f} ms")   # → [F4]

    # ③-5 판정
    result = judge(score_a, score_b, "A", "B")            # → [F3]
    if result == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {result}")

    # ③-6 성능 표 (3×3)
    print_performance([3])                                # → [F10]


# [F13] ④-3 패턴 1개 검사·판정
#       돌려주는 값: 통과하면 None, 실패하면 실패 사유(글자)
def check_case(key, case, filters):
    # ④-3-1 키 'size_13_1'에서 크기 13을 꺼낸다
    n = int(key.split("_")[1])

    # ④-3-2 데이터 검사: 맞는 필터가 있는지, 패턴 크기가 맞는지
    if n not in filters:
        return f"size_{n} 필터 없음"
    pattern = case["input"]
    if not is_size(pattern, n):                           # → [F7]
        return f"크기 불일치: 필터는 {n}×{n}인데 패턴 크기가 다름"

    # ④-3-3 점수 계산과 판정
    expected = normalize(case["expected"])                # → [F1]  '+' → 'Cross'
    cross_score = mac(pattern, filters[n]["Cross"])       # → [F2]
    x_score = mac(pattern, filters[n]["X"])               # → [F2]
    result = judge(cross_score, x_score, "Cross", "X")    # → [F3]

    print(f"Cross 점수: {cross_score}")
    print(f"X 점수: {x_score}")

    # ④-3-4 정답(expected)과 비교해 PASS / FAIL
    if result == "UNDECIDED":
        print(f"판정: {result} | expected: {expected} | FAIL (동점 규칙)")
        return "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
    if result != expected:
        print(f"판정: {result} | expected: {expected} | FAIL")
        return f"판정 {result}, expected {expected}"
    print(f"판정: {result} | expected: {expected} | PASS")
    return None


# [F14] ④ 모드 2: data.json 분석 모드
def json_mode():
    # ④-1 data.json 파일 읽기
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)

    # ④-2 필터 로드: filters[크기] = {"Cross": 표, "X": 표}
    print_title("[1] 필터 로드")
    filters = {}
    for key, pair in data["filters"].items():
        n = int(key.split("_")[1])                        # 'size_5' → 5
        filters[n] = {}
        for name, grid in pair.items():
            filters[n][normalize(name)] = grid            # → [F1]  'cross' → 'Cross'
        print(f"✓ {key:<8}필터 로드 완료 (Cross, X)")

    # ④-3 패턴을 하나씩 검사·판정
    print_title("[2] 패턴 분석 (라벨 정규화 적용)")
    failures = []                                         # (케이스 이름, 실패 사유) 목록
    for key, case in data["patterns"].items():
        print(f"--- {key} ---")
        try:
            reason = check_case(key, case, filters)       # → [F13]
        except (KeyError, IndexError, ValueError, TypeError) as error:
            # 데이터가 깨져 있어도 프로그램을 멈추지 않고 이 케이스만 FAIL 처리
            reason = f"데이터 형식 오류 ({error})"
        if reason is not None:
            failures.append((key, reason))
            if "판정" not in reason and "동점" not in reason:
                print(f"FAIL: {reason}")                  # 계산 전에 걸린 오류만 여기서 출력

    # ④-4 성능 표 (3×3 + data.json에 있는 크기들)
    print_performance([3] + sorted(filters))              # → [F10]

    # ④-5 결과 요약
    print_title("결과 요약")
    total = len(data["patterns"])
    print(f"총 테스트: {total}개")
    print(f"통과: {total - len(failures)}개")
    print(f"실패: {len(failures)}개")
    if failures:
        print("\n실패 케이스:")
        for key, reason in failures:
            print(f"- {key}: {reason}")


# [F15] ② 모드 선택
def main():
    print("=== Mini NPU Simulator ===\n")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    if input("선택: ").strip() == "1":
        user_mode()                                       # → ③ [F12]
    else:
        json_mode()                                       # → ④ [F14]


# ① 프로그램 시작점: 여기서 main()을 부르며 모든 것이 시작된다 → [F15]
main()
