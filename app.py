import streamlit as st
import pandas as pd
import numpy as np
import time

# 페이지 설정
st.set_page_config(page_title="사회 현상 시뮬레이터", page_icon="📈", layout="centered")

st.title("🌐 사회 현상 시뮬레이터: 유행 확산과 동적 흥미")
st.markdown("집단 내 유행 참여율이 높아질수록 흥미가 더 오래 지속되는 현상을 시뮬레이션합니다.")

# 사이드바 설정 (입력 위젯)
st.sidebar.header("⚙️ 시뮬레이터 설정")
num_people = st.sidebar.slider("전체 인원 수", min_value=50, max_value=200, value=100, step=10)
infection_chance = st.sidebar.slider("전파 확률 (%)", min_value=5, max_value=100, value=40) / 100.0
base_duration = st.sidebar.slider("기본 흥미 지속 시간 (턴)", min_value=5, max_value=50, value=15)
dynamic_weight = st.sidebar.slider("동적 가중치 (참여도 비례 지속 증가)", min_value=0, max_value=50, value=20)
max_turns = st.sidebar.slider("최대 시뮬레이션 턴 수", min_value=20, max_value=200, value=100, step=10)

# 세션 상태 초기화 (데이터 유지용)
if 'initialized' not in st.session_state or st.sidebar.button("🔄 초기화 / 새로고침"):
    st.session_state['initialized'] = True
    # 에이전트 위치 및 상태 초기화 (0: 미참여, 1: 참여 중, 2: 흥미 종료)
    np.random.seed(42)
    st.session_state['x'] = np.random.rand(num_people) * 300
    st.session_state['y'] = np.random.rand(num_people) * 300
    st.session_state['vx'] = (np.random.rand(num_people) - 0.5) * 5
    st.session_state['vy'] = (np.random.rand(num_people) - 0.5) * 5
    st.session_state['state'] = np.zeros(num_people, dtype=int)
    st.session_state['timer'] = np.zeros(num_people, dtype=int)
    
    # 초기 전파자 3명 설정
    initial_infected = np.random.choice(num_people, 3, replace=False)
    st.session_state['state'][initial_infected] = 1
    st.session_state['timer'][initial_infected] = base_duration
    st.session_state['turn'] = 0
    st.session_state['history'] = []

# 레이아웃 구성
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("📊 실시간 통계")
    turn_placeholder = st.empty()
    active_placeholder = st.empty()
    recovered_placeholder = st.empty()
    susceptible_placeholder = st.empty()
    
    start_button = st.button("▶ 시뮬레이션 실행", type="primary")

with col1:
    st.subheader("🖥️ 시각화 화면")
    chart_placeholder = st.empty()

# 시뮬레이션 한 턴 진행 함수
def step_simulation():
    turn = st.session_state['turn']
    if turn >= max_turns:
        return False

    turn += 1
    st.session_state['turn'] = turn

    x = st.session_state['x']
    y = st.session_state['y']
    vx = st.session_state['vx']
    vy = st.session_state['vy']
    state = st.session_state['state']
    timer = st.session_state['timer']

    # 위치 이동 (벽에 부딪히면 반사)
    x += vx
    y += vy
    vx = np.where((x < 0) | (x > 300), -vx, vx)
    vy = np.where((y < 0) | (y > 300), -vy, vy)
    x = np.clip(x, 0, 300)
    y = np.clip(y, 0, 300)

    st.session_state['x'] = x
    st.session_state['y'] = y
    st.session_state['vx'] = vx
    st.session_state['vy'] = vy

    # 현재 참여자 비율 계산
    active_indices = (state == 1)
    active_count = np.sum(active_indices)
    active_ratio = active_count / num_people if num_people > 0 else 0

    # 동적 흥미 지속 시간 적용
    current_duration = int(base_duration + (active_ratio * dynamic_weight))

    # 1. 참여 중인 사람 타이머 감소 및 종료 처리
    if active_count > 0:
        timer[active_indices] -= 1
        expired = (state == 1) & (timer <= 0)
        state[expired] = 2  # 흥미 종료

    # 2. 전파 처리 (참유 중인 사람 근처의 미참여자에게 전파)
    susceptible_indices = np.where(state == 0)[0]
    active_indices_list = np.where(state == 1)[0]

    new_infected = []
    if len(active_indices_list) > 0 and len(susceptible_indices) > 0:
        for p in susceptible_indices:
            # 거리 계산
            distances = np.hypot(x[p] - x[active_indices_list], y[p] - y[active_indices_list])
            if np.any(distances < 35):  # 35 이내 근접 시
                if np.random.rand() < infection_chance:
                    new_infected.append(p)

    if new_infected:
        state[new_infected] = 1
        timer[new_infected] = current_duration

    st.session_state['state'] = state
    st.session_state['timer'] = timer

    # 통계 기록 저장
    susceptible_count = np.sum(state == 0)
    recovered_count = np.sum(state == 2)
    st.session_state['history'].append({
        "Turn": turn,
        "Active": active_count,
        "Recovered": recovered_count,
        "Susceptible": susceptible_count
    })

    return True

# 버튼 클릭 시 실행 루프
if start_button:
    progress_bar = st.progress(0)
    for t in range(max_turns):
        running = step_simulation()
        if not running:
            break
        
        # 통계 텍스트 업데이트
        turn_placeholder.markdown(f"**경과 턴:** {st.session_state['turn']} / {max_turns}")
        active_placeholder.markdown(f"🔴 **참여 중:** {np.sum(st.session_state['state'] == 1)}명")
        recovered_placeholder.markdown(f"🔵 **흥미 종료:** {np.sum(st.session_state['state'] == 2)}명")
        susceptible_placeholder.markdown(f"⚪ **미참여:** {np.sum(st.session_state['state'] == 0)}명")

        # 산점도(Scatter Plot) 시각화 데이터 준비
        df_plot = pd.DataFrame({
            'x': st.session_state['x'],
            'y': st.session_state['y'],
            'status': ['미참여' if s==0 else ('참여 중' if s==1 else '흥미 종료') for s in st.session_state['state']]
        })
        
        # Streamlit 내장 차트로 위치 및 상태 표시
        chart_placeholder.scatter_chart(df_plot, x='x', y='y', color='status', size=50, height=300)
        
        progress_bar.progress((t + 1) / max_turns)
        time.sleep(0.1) # 애니메이션 속도 조절
    
    st.success("시뮬레이션이 완료되었습니다!")

# 초기 상태 화면에 반영
turn_placeholder.markdown(f"**경과 턴:** {st.session_state['turn']} / {max_turns}")
active_placeholder.markdown(f"🔴 **참여 중:** {np.sum(st.session_state['state'] == 1)}명")
recovered_placeholder.markdown(f"🔵 **흥미 종료:** {np.sum(st.session_state['state'] == 2)}명")
susceptible_placeholder.markdown(f"⚪ **미참여:** {np.sum(st.session_state['state'] == 0)}명")

df_plot = pd.DataFrame({
    'x': st.session_state['x'],
    'y': st.session_state['y'],
    'status': ['미참여' if s==0 else ('참여 중' if s==1 else '흥미 종료') for s in st.session_state['state']]
})
chart_placeholder.scatter_chart(df_plot, x='x', y='y', color='status', size=50, height=300)
