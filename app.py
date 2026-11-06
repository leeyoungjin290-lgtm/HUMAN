import streamlit as st
import pandas as pd
import numpy as np
import time

# 페이지 설정
st.set_page_config(page_title="기계·상품 유행 및 장기 정착 시뮬레이터", page_icon="📈", layout="centered")

st.title("🌐 기계·상품 유행 및 장기 정착 시뮬레이터 (고정 격자형)")
st.markdown("소비자들이 고정된 위치에서 입소문과 실용성에 따라 유행을 확산시키고 정착시키는 과정을 시뮬레이션합니다.")

# 1. 사이드바 변인 설정 (입력)
st.sidebar.header("⚙️ 변인 설정 (입력)")
grid_side = st.sidebar.slider("격자 한 변의 크기 (N x N)", min_value=8, max_value=16, value=12, step=2)
total_people = grid_side * grid_side

seed_count = st.sidebar.slider("초기 유행 전파자 (Seed)", min_value=1, max_value=10, value=3)
transmission_rate = st.sidebar.slider("전파 확률 (입소문/광고 효과, %)", min_value=5, max_value=100, value=40) / 100.0
base_duration = st.sidebar.slider("기본 흥미 지속 시간 (턴)", min_value=1, max_value=20, value=5)
dynamic_weight = st.sidebar.slider("실용성/만족도 동적 가중치", min_value=0, max_value=30, value=10)
max_turns = st.sidebar.slider("최대 시뮬레이션 턴 수", min_value=10, max_value=100, value=50, step=5)

# 세션 상태 초기화 (고정 격자 생성)
if 'initialized' not in st.session_state or st.sidebar.button("🔄 초기화 / 새로고침"):
    st.session_state['initialized'] = True
    st.session_state['side'] = grid_side
    
    # 0: 미체험 (Susceptible), 1: 참여 중 (Active), 2: 흥미 종료/이탈 (Recovered)
    grid_state = np.zeros((grid_side, grid_side), dtype=int)
    grid_timer = np.zeros((grid_side, grid_side), dtype=int)
    
    # 초기 전파자 무작위 배치
    np.random.seed(int(time.time()))
    seeded = 0
    while seeded < seed_count:
        rx = np.random.randint(0, grid_side)
        ry = np.random.randint(0, grid_side)
        if grid_state[rx, ry] == 0:
            grid_state[rx, ry] = 1
            grid_timer[rx, ry] = base_duration
            seeded += 1
            
    st.session_state['grid_state'] = grid_state
    st.session_state['grid_timer'] = grid_timer
    st.session_state['turn'] = 0
    st.session_state['history'] = []

# 레이아웃 구성
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("📊 실시간 관찰 결과")
    turn_display = st.empty()
    active_display = st.empty()
    recovered_display = st.empty()
    susceptible_display = st.empty()
    
    start_button = st.button("▶ 시뮬레이션 시작", type="primary")

with col1:
    st.subheader("🖥️ 고정 격자 시각화")
    grid_display = st.empty()

# 시뮬레이션 1턴 진행 로직 (고정 격자 상하좌우 전파)
def step_simulation():
    side = st.session_state['side']
    state = st.session_state['grid_state'].copy()
    timer = st.session_state['grid_timer'].copy()
    turn = st.session_state['turn']

    if turn >= max_turns:
        return False

    # 현재 참여율 계산 (동적 흥미 지속 시간 적용)
    active_count = np.sum(state == 1)
    active_ratio = active_count / (side * side)
    current_dynamic_duration = int(base_duration + (active_ratio * dynamic_weight))

    next_state = state.copy()
    next_timer = timer.copy()

    # 1. 기존 참여자의 흥미 지속 시간 감소 처리
    for r in range(side):
        for c in range(side):
            if state[r, c] == 1:
                next_timer[r, c] -= 1
                if next_timer[r, c] <= 0:
                    next_state[r, c] = 2 # 흥미 종료(이탈)

    # 2. 상하좌우 이웃 전파 처리
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for r in range(side):
        for c in range(side):
            if state[r, c] == 1:
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < side and 0 <= nc < side:
                        if state[nr, nc] == 0 and next_state[nr, nc] == 0:
                            if np.random.rand() < transmission_rate:
                                next_state[nr, nc] = 1
                                next_timer[nr, nc] = max(1, current_dynamic_duration)

    st.session_state['grid_state'] = next_state
    st.session_state['grid_timer'] = next_timer
    st.session_state['turn'] = turn + 1
    return True

# 화면에 고정 격자 그리는 함수
def render_grid():
    side = st.session_state['side']
    state = st.session_state['grid_state']
    
    rows, cols = [], []
    statuses = []
    
    for r in range(side):
        for c in range(side):
            rows.append(r)
            cols.append(c)
            s = state[r, c]
            statuses.append('미체험' if s == 0 else ('참여 중(유행)' if s == 1 else '흥미 종료(이탈)'))

    df_grid = pd.DataFrame({'x': cols, 'y': rows, '상태': statuses})
    grid_display.scatter_chart(df_grid, x='x', y='y', color='상태', size=120, height=350)

# 시뮬레이션 실행 루프
if start_button:
    progress_bar = st.progress(0)
    for t in range(max_turns):
        running = step_simulation()
        
        # 통계 지표 업데이트
        current_turn = st.session_state['turn']
        state = st.session_state['grid_state']
        side = st.session_state['side']
        total = side * side
        
        active_cnt = np.sum(state == 1)
        recovered_cnt = np.sum(state == 2)
        susceptible_cnt = np.sum(state == 0)

        turn_display.markdown(f"**경과 턴:** {current_turn} / {max_turns}")
        active_display.markdown(f"🔴 **참여 중(유행):** {active_cnt}명 ({active_cnt/total*100:.1f}%)")
        recovered_display.markdown(f"🔵 **흥미 종료(이탈):** {recovered_cnt}명")
        susceptible_display.markdown(f"⚪ **미체험:** {susceptible_cnt}명")

        render_grid()
        progress_bar.progress((t + 1) / max_turns)
        
        if active_cnt == 0 or not running:
            break
            
        time.sleep(0.15)
    
    st.success("시뮬레이션이 완료되었습니다!")

# 초기 상태 출력
turn_display.markdown(f"**경과 턴:** {st.session_state['turn']} / {max_turns}")
state = st.session_state['grid_state']
side = st.session_state['side']
total = side * side

active_cnt = np.sum(state == 1)
recovered_cnt = np.sum(state == 2)
susceptible_cnt = np.sum(state == 0)

active_display.markdown(f"🔴 **참여 중(유행):** {active_cnt}명 ({active_cnt/total*100:.1f}%)")
recovered_display.markdown(f"🔵 **흥미 종료(이탈):** {recovered_cnt}명")
susceptible_display.markdown(f"⚪ **미체험:** {susceptible_cnt}명")

render_grid()
