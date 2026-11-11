import streamlit as st
import numpy as np
import pandas as pd
import time

# 1. 페이지 설정
st.set_page_config(page_title="신상품 유행 확산 시뮬레이터", layout="wide")

st.title("📉 신상품 유행 확산 및 지속성 분석 시뮬레이터")
st.caption("초기 전파 확률과 실용성 만족도에 따른 유행 변화 양상 분석")

# ---------------------------------------------------------
# 2. 사이드바: 변인 설정
# ---------------------------------------------------------
st.sidebar.header("⚙️ 실험 변인 설정")

total_agents = st.sidebar.number_input("전체 잠재 소비자 수 (N)", value=100, step=10)
max_turns = st.sidebar.slider("최대 진행 턴 수", min_value=30, max_value=200, value=50, step=10)

base_duration = st.sidebar.slider("기본 흥미 지속 시간 (턴)", min_value=1, max_value=50, value=15)
infection_prob = st.sidebar.slider("초기 전파 확률 (%)", min_value=5, max_value=100, value=50, step=5) / 100.0
satisfaction_weight = st.sidebar.slider("실용성/만족도 가중치 (동적 보너스)", min_value=0.0, max_value=2.0, value=0.5, step=0.1)
initial_adopters = st.sidebar.slider("초기 얼리어답터 수", min_value=1, max_value=20, value=5)

# ---------------------------------------------------------
# 3. 세션 상태 초기화 (초기화 버튼 포함)
# ---------------------------------------------------------
def initialize_simulation():
    st.session_state.turn = 0
    st.session_state.running = False
    st.session_state.states = np.zeros(total_agents, dtype=int) # 0: 미체험, 1: 참여, 2: 이탈
    st.session_state.states[:initial_adopters] = 1
    
    st.session_state.remaining = np.zeros(total_agents, dtype=int)
    st.session_state.remaining[:initial_adopters] = base_duration
    
    st.session_state.history = [{
        "턴": 0,
        "미체험자": int(np.sum(st.session_state.states == 0)),
        "참여 중": int(np.sum(st.session_state.states == 1)),
        "이탈자": int(np.sum(st.session_state.states == 2))
    }]

if "states" not in st.session_state or len(st.session_state.states) != total_agents:
    initialize_simulation()

# 리셋 버튼
if st.sidebar.button("🔄 시뮬레이션 초기화"):
    initialize_simulation()
    st.rerun()

# ---------------------------------------------------------
# 4. 턴 진행 함수 (오류 방어 코드 추가)
# ---------------------------------------------------------
def advance_turn():
    if st.session_state.turn >= max_turns:
        st.session_state.running = False
        return

    states = st.session_state.states
    remaining = st.session_state.remaining

    remaining = np.asarray(remaining, dtype=int)

    active_indices = np.where(states == 1)[0]
    unexposed_indices = np.where(states == 0)[0]

    active_count = len(active_indices)
    active_ratio = active_count / total_agents if total_agents > 0 else 0

    contact_prob = np.clip(active_ratio * infection_prob, 0.0, 1.0)

    # ① 미체험자의 신규 참여
    if active_count > 0 and len(unexposed_indices) > 0:
        random_values = np.random.random(len(unexposed_indices))
        new_adopters = unexposed_indices[random_values < contact_prob]
    else:
        new_adopters = np.array([], dtype=int)

    # ② 기존 참여자의 흥미 지속 시간 감소
    if len(active_indices) > 0:
        remaining[active_indices] -= 1
        expired_indices = active_indices[remaining[active_indices] <= 0]
        states[expired_indices] = 2
        remaining[expired_indices] = 0

    # ③ 신규 참여자 등록
    dynamic_bonus = base_duration * satisfaction_weight * active_ratio
    new_duration = max(1, int(round(base_duration + dynamic_bonus)))

    if len(new_adopters) > 0:
        states[new_adopters] = 1
        remaining[new_adopters] = new_duration

    # ④ 이탈자의 재참여
    return_prob = np.clip(satisfaction_weight * 0.25, 0.0, 1.0)
    dropped_indices = np.where(states == 2)[0]

    if len(dropped_indices) > 0:
        random_values = np.random.random(len(dropped_indices))
        returning_users = dropped_indices[random_values < return_prob]
        if len(returning_users) > 0:
            states[returning_users] = 1
            remaining[returning_users] = new_duration

    # ⑤ 상태 저장
    st.session_state.states = states
    st.session_state.remaining = remaining

    # ⑥ 턴 증가 및 기록
    st.session_state.turn += 1
    st.session_state.history.append({
        "턴": st.session_state.turn,
        "미체험자": int(np.sum(states == 0)),
        "참여 중": int(np.sum(states == 1)),
        "이탈자": int(np.sum(states == 2))
    })

    if st.session_state.turn >= max_turns:
        st.session_state.running = False

# ---------------------------------------------------------
# 5. UI 컨트롤 및 대시보드 레이아웃
# ---------------------------------------------------------
col_btn1, col_btn2, col_btn3 = st.columns(3)
with col_btn1:
    if st.button("▶️ 1턴씩 진행"):
        advance_turn()
        st.rerun()
with col_btn2:
    if st.button("🚀 전체 자동 실행"):
        st.session_state.running = True
with col_btn3:
    if st.button("⏹️ 일시 정지"):
        st.session_state.running = False

# 자동 실행 로직 (while 루프 대신 st.rerun 활용하여 흰 화면 방지)
if st.session_state.get("running", False):
    if st.session_state.turn < max_turns:
        advance_turn()
        time.sleep(0.1) # 애니메이션 속도 조절
        st.rerun()
    else:
        st.session_state.running = False

# ---------------------------------------------------------
# 6. 결과 시각화 및 지표 출력
# ---------------------------------------------------------
st.divider()

df_history = pd.DataFrame(st.session_state.history)

col_chart, col_metrics = st.columns([2, 1])

with col_chart:
    st.subheader(f"📊 실시간 유행 변화 (현재 턴: {st.session_state.turn} / {max_turns})")
    if not df_history.empty:
        # Streamlit 내장 라인 차트 사용 (matplotlib 오류 원천 차단)
        st.line_chart(df_history.set_index("턴")[["미체험자", "참여 중", "이탈자"]], color=["#808080", "#FF4B4B", "#1E88E5"])

with col_metrics:
    st.subheader("📌 핵심 지표")
    current_active = int(np.sum(st.session_state.states == 1))
    current_dropped = int(np.sum(st.session_state.states == 2))
    retention_rate = (current_active / total_agents) * 100

    st.metric("현재 참여 중인 인원", f"{current_active} 명")
    st.metric("누적 이탈자 수", f"{current_dropped} 명")
    st.metric("현재 참여율", f"{retention_rate:.1f} %")

st.markdown("### 📋 기록 데이터 테이블")
st.dataframe(df_history.tail(10), use_container_width=True)
