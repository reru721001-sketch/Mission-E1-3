# Mini NPU Simulator

MAC 연산으로 그림이 십자가(Cross)인지 X인지 판별하는 Python 콘솔 프로그램입니다.

## 1. 실행 방법

- Python 3.8 이상, 외부 라이브러리 없음
- `data.json`을 `main.py`와 같은 폴더에 두고 실행

```
python main.py
```

```python
with open("data.json", encoding="utf-8") as f:    # 같은 폴더의 data.json을 읽음
    data = json.load(f)
```

## 2. 모드 선택

- `1` 사용자 입력: 3×3 필터 A, B와 패턴을 한 줄씩 공백으로 구분해 입력
  - 다시 `2`를 고르면 크기 N을 입력해 십자가와 X를 자동 생성 (보너스: 패턴 생성기)
- `2` data.json 분석: 패턴 6개를 판정하고 정답과 비교해 PASS/FAIL 출력

```python
def main():
    print("=== Mini NPU Simulator ===\n")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    if input("선택: ").strip() == "1":
        user_mode()       # 모드 1
    else:
        json_mode()       # 모드 2
```

## 3. 라벨 정규화

- data.json의 표기가 제각각이라(`+`, `cross`, `x`) 모두 `Cross` / `X`로 통일한 뒤 비교합니다.
- 통일하지 않으면 컴퓨터는 `+`와 `Cross`를 다른 글자로 봐서, 정답을 맞혀도 FAIL이 됩니다.

```python
LABELS = {"+": "Cross", "cross": "Cross", "x": "X"}

def normalize(label):
    return LABELS.get(str(label).lower())
```

## 4. MAC 연산

- 그림과 필터를 겹쳐 같은 칸끼리 곱하고(Multiply) 모두 더합니다(Accumulate).
- NumPy 없이 이중 `for`문으로 직접 구현했습니다.
- 두 필터 중 점수가 높은 쪽으로 판정합니다.

```python
def mac(pattern, filter_grid):
    n = len(pattern)
    total = 0.0
    for i in range(n):              # i = 가로줄(행) 번호
        for j in range(n):          # j = 세로줄(열) 번호
            total += pattern[i][j] * filter_grid[i][j]
    return total
```

## 5. 동점 처리 정책 (epsilon)

- 컴퓨터의 소수 계산에는 미세한 오차가 있습니다. (`0.1 + 0.2 = 0.30000000000000004`)
- 두 점수 차이가 `1e-9`보다 작으면 동점으로 보고 `UNDECIDED`(판정 불가)로 처리합니다.

```python
EPSILON = 1e-9

def judge(score_a, score_b, name_a, name_b):
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    if score_a > score_b:
        return name_a
    return name_b
```

## 6. 실패 원인 분석

- 결과: 총 6개 / 통과 3개 / 실패 3개 (size_5_1, size_13_2, size_25_1)
- 데이터 문제 아님: 모든 패턴이 필터와 크기가 맞고, 라벨은 정규화로 통일했습니다.
- 로직 문제 아님: 점수 차이가 뚜렷한 3개는 모두 PASS했습니다.
- 수치 비교 문제: 실패 3개는 두 점수가 사실상 같습니다. (예: 0.9 vs 0.8999999999999999)
- size_5_1의 그림은 X지만, data.json의 X 필터는 0.1 × 9칸 = 0.9, 십자가 필터는 0.9 × 1칸 = 0.9로 원래 같은 점수가 나오게 되어 있습니다.
- X 점수는 0.1을 9번 더하며 오차가 쌓여 0.8999999999999999가 됐습니다.
- epsilon 규칙대로 동점(UNDECIDED) 처리했고, 정답 X와 다르니 FAIL입니다. 버그가 아닙니다.

```python
# 데이터 검사: 맞는 필터가 있는지, 패턴 크기가 맞는지
if n not in filters:
    return f"size_{n} 필터 없음"
if not is_size(pattern, n):
    return f"크기 불일치: 필터는 {n}×{n}인데 패턴 크기가 다름"

# 판정 결과를 정답(expected)과 비교
if result == "UNDECIDED":
    print(f"판정: {result} | expected: {expected} | FAIL (동점 규칙)")
    return "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
if result != expected:
    print(f"판정: {result} | expected: {expected} | FAIL")
    return f"판정 {result}, expected {expected}"
print(f"판정: {result} | expected: {expected} | PASS")
```

## 7. 시간 복잡도 분석

| 크기 | 평균 시간(ms, 10회) | 연산 횟수(N²) |
|---|---|---|
| 3×3 | 0.0024 | 9 |
| 5×5 | 0.0037 | 25 |
| 13×13 | 0.0167 | 169 |
| 25×25 | 0.0637 | 625 |

- N×N 그림은 칸이 N²개라서 곱셈도 N²번 합니다. → **O(N²)**
- 5×5 → 25×25: 크기는 5배, 연산 횟수는 25배, 시간은 약 17배 늘었습니다.
- 크기보다 훨씬 많이 늘었으므로 시간이 N²을 따라 늘어난다는 것을 확인했습니다.
- 딱 25배가 아닌 이유는 크기와 상관없이 항상 드는 기본 시간(함수 호출 등)이 섞여 있기 때문입니다.

```python
REPEAT = 10

def measure_ms(pattern, filter_grid):
    start = time.perf_counter()
    for _ in range(REPEAT):                 # MAC 계산만 10번 반복
        mac(pattern, filter_grid)
    return (time.perf_counter() - start) / REPEAT * 1000   # 1회 평균(ms)
```
