import streamlit as st
import pandas as pd
import numpy as np
import time

# 페이지 설정
st.set_page_config(page_title="기계 상품 유행 및 장기 정착 시뮬레이터", page_icon="📈", layout="centered")

st.title("🌐 기계·상품 유행 및 장기 정착 시뮬레이터")
st.markdown("새로운 상품이 반짝 유행에 그치지 않고 필수품으로 정착하는 과정을 시뮬레이션합니다.")

# 1. 사이드바 설정 (변인 설정)
st.sidebar.header("⚙️ 변인 설정 (입력)")
num_people = st.sidebar.slider("전체 잠재 소비자 수", min_value=50, max_value=200, value=100, step=10)
infection_chance = st.sidebar.slider("전파 확률 (입소문/광고 효과, %)", min_value=5, max_value=100, value=40) / 100.0
base_duration = st.sidebar.slider("기본 흥미 지속 시간 (턴)", min_value=5, max_value=50, value=15)
dynamic_weight = st.sidebar.slider("실용성/만족도 동적 가중치", min_value=0, max_value=50, value=20)
max_turns = st.sidebar.slider("최대 시뮬레이션 턴 수", min_value=20, max_value=200, value=100, step=10)

# 세션 상태 초기화 (초기화 버튼 연동)
if 'initialized' not in st.session_state or st.sidebar.button("🔄 초기화 / 새로고침"):
    st.session_state['initialized'] = True
    np.random.seed(42)
    st.session_state['x'] = np.random.rand(num_people) * 300
    st.session_state['y'] = np.random.rand(num_people) * 300
    st.session_state['vx'] = (np.random.rand(num_people) - 0.5) * 4
    st.session_state['vy'] = (np.random.rand(num_people) - 0.5) * 4
    st.session_state['state'] = np.zeros(num_people, dtype=int) # 0: 미체험, 1: 참여 중(유행), 2: 흥미 종료(이탈)
    st.session_state['timer'] = np.zeros(num_people, dtype=int)
    
    # 초기 유행 전파자 3명 설정
    initial_infected = np.random.choice(num_people, 3, replace=False)
    st.session_state['state'][initial_infected] = 1
    st.session_state['timer'][initial_infected] = base_duration
    st.session_state['turn'] = 0

# 레이아웃 구성 (좌측: 시각화 화면, 우측: 실시간 통계)
col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("📊 실시간 관찰 결과")
    turn_display = st.empty()
    active_display = st.empty()
    recovered_display = st.empty()
    susceptible_display = st.empty()
    
    start_button = st.button("▶ 시뮬레이션 시작", type="primary")

with col1:
    st.subheader("🖥️ 시뮬레이션 화면")
    chart_display = st.empty()

# 시뮬레이션 1턴 진행 모델 규칙 함수
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

    # 에이전트 이동 및 벽 반사 처리
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

    # 현재 유행 참여율 계산
    active_indices = (state == 1)
    active_count = np.sum(active_indices)
    active_ratio = active_count / num_people if num_people > 0 else 0

    # 계산 규칙: 집단 참여율이 높을수록(동적 효과) 흥미 지속 시간 연장
    current_duration = int(base_duration + (active_ratio * dynamic_weight))

    # 1. 참여 중인 소비자의 타이머 감소 및 이탈 처리
    if active_count > 0:
        timer[active_indices] -= 1
        expired = (state == 1) & (timer <= 0)
        state[expired] = 2  # 흥미 종료 (이탈)

    # 2. 전파 규칙: 미체험자가 주변의 '참여 중'인 소비자를 만나면 전파 확률에 따라 체험 시작
    susceptible_indices = np.where(state == 0)[0]
    active_indices_list = np.where(state == 1)[0]

    new_infected = []
    if len(active_indices_list) > 0 and len(susceptible_indices) > 0:
        for p in susceptible_indices:
            distances = np.hypot(x[p] - x[active_indices_list], y[p] - y[active_indices_list])
            if np.any(distances < 35):  # 상호작용 거리 35 이내
                if np.random.rand() < infection_chance:
                    new_infected.append(p)

    if new_infected:
        state[new_infected] = 1
        timer[new_infected] = current_duration

    st.session_state['state'] = state
    st.session_state['timer'] = timer
    return True

# 실행 버튼 클릭 시 애니메이션 루프
if start_button:
    progress_bar = st.progress(0)
    for t in range(max_turns):
        running = step_simulation()
        if not running:
            break
        
        # 통계 지표 업데이트
        current_turn = st.session_state['turn']
        active_cnt = np.sum(st.session_state['state'] == 1)
        recovered_cnt = np.sum(st.session_state['state'] == 2)
        susceptible_cnt = np.sum(st.session_state['state'] == 0)

        turn_display.markdown(f"**경과 턴:** {current_turn} / {max_turns}")
        active_display.markdown(f"🔴 **참여 중(유행):** {active_cnt}명")
        recovered_display.markdown(f"🔵 **흥미 종료(이탈):** {recovered_cnt}명")
        susceptible_display.markdown(f"⚪ **미체험:** {susceptible_cnt}명")

        # 시각화 화면 업데이트 (산점도)
        df_plot = pd.DataFrame({
            'x': st.session_state['x'],
            'y': st.session_state['y'],
            '상태': ['미체험' if s==0 else ('참여 중' if s==1 else '흥미 종료') for s in st.session_state['state']]
        })
        chart_display.scatter_chart(df_plot, x='x', y='y', color='상태', size=50, height=300)
        
        progress_bar.progress((t + 1) / max_turns)
        time.sleep(0.1)
    
    st.success("시뮬레이션이 완료되었습니다!")

# 초기 대기 화면 출력
turn_display.markdown(f"**경과 턴:** {st.session_state['turn']} / {max_turns}")
active_display.markdown(f"🔴 **참여 중(유행):** {np.sum(st.session_state['state'] == 1)}명")
recovered_display.markdown(f"🔵 **흥미 종료(이탈):** {np.sum(st.session_state['state'] == 2)}명")
susceptible_display.markdown(f"⚪ **미체험:** {np.sum(st.session_state['state'] == 0)}명")

df_plot = pd.DataFrame({
    'x': st.session_state['x'],
    'y': st.session_state['y'],
    '상태': ['미체험' if s==0 else ('참여 중' if s==1 else '흥미 종료') for s in st.session_state['state']]
})
chart_display.scatter_chart(df_plot, x='x', y='y', color='상태', size=50, height=300)
