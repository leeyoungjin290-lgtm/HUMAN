import time

import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="사용자 변화 시뮬레이션",
    page_icon="🔲",
    layout="wide"
)

st.title("사용자 변화 시뮬레이션")
st.write("사용자의 확산, 흥미 감소, 폐기를 관찰합니다.")

# --------------------------------------------------
# 내부 고정값 (흥미 정도 / 만족도 1.0 기준)
# --------------------------------------------------

STEP_DELAY = 0.1             # 전체 실행 시 턴 사이 대기 시간(초)

BASE_DURATION = 10           # 흥미 정도 1.0일 때 흥미 지속 턴
SATISFACTION_BASE_PROB = 0.1     # 만족도 1.0일 때 매 턴 만족 발생 확률
SATISFACTION_BASE_EXTENSION = 5  # 만족도 1.0일 때 만족으로 늘어나는 턴

# --------------------------------------------------
# 설정
# --------------------------------------------------

st.sidebar.header("시뮬레이션 설정")

N = st.sidebar.number_input(
    "전체 참여 대상 수",
    min_value=10,
    max_value=400,
    value=100,
    step=10
)

initial_users = st.sidebar.number_input(
    "초기 사용자 수",
    min_value=1,
    max_value=int(N),
    value=min(5, int(N))
)

max_turns = st.sidebar.slider(
    "최대 턴 수", 10, 200, 50
)

interest_level = st.sidebar.slider(
    "흥미 정도", 0.0, 2.0, 1.0, 0.05,
    help="높을수록 유행에 참여할 확률과 흥미 지속 턴이 늘어납니다."
)

satisfaction_level = st.sidebar.slider(
    "만족도", 0.0, 2.0, 1.0, 0.05,
    help="높을수록 흥미 지속 중 만족이 발생할 확률과 "
         "만족으로 늘어나는 흥미 지속 턴이 커집니다."
)

# --------------------------------------------------
# 흥미 정도 / 만족도로부터 계산되는 값
# --------------------------------------------------

# 흥미 정도 -> 흥미 지속 턴
interest_duration = max(
    1,
    int(round(BASE_DURATION * interest_level))
)

# 만족도 -> 만족 발생 확률
satisfaction_prob = float(np.clip(
    satisfaction_level * SATISFACTION_BASE_PROB,
    0.0,
    1.0
))

# 만족도 -> 만족 시 늘어나는 흥미 지속 턴
satisfaction_extension = max(
    1,
    int(round(SATISFACTION_BASE_EXTENSION * satisfaction_level))
)

# --------------------------------------------------
# 초기화
# --------------------------------------------------

def reset_simulation():

    states = np.zeros(int(N), dtype=int)
    remaining = np.zeros(int(N), dtype=int)

    states[:int(initial_users)] = 1
    remaining[:int(initial_users)] = interest_duration

    st.session_state.states = states
    st.session_state.remaining = remaining
    st.session_state.turn = 0
    st.session_state.running = True

    st.session_state.history = [{
        "턴": 0,
        "미체험자": int(np.sum(states == 0)),
        "참여 중": int(np.sum(states == 1)),
        "폐기": int(np.sum(states == 2))
    }]


# --------------------------------------------------
# 세션 초기화 및 설정 변경 확인
# --------------------------------------------------

settings = (
    int(N),
    int(initial_users),
    int(max_turns),
    float(interest_level),
    float(satisfaction_level)
)

if (
    "settings" not in st.session_state
    or st.session_state.settings != settings
):
    st.session_state.settings = settings
    reset_simulation()


# --------------------------------------------------
# 한 턴 진행
# --------------------------------------------------

def advance_turn():

    if not st.session_state.running:
        return

    if st.session_state.turn >= max_turns:
        st.session_state.running = False
        return

    states = st.session_state.states.copy()
    remaining = st.session_state.remaining.copy()

    # 턴 시작 시 상태별 대상 확인
    active_indices = np.where(states == 1)[0]
    unexposed_indices = np.where(states == 0)[0]

    active_count = len(active_indices)
    active_ratio = active_count / N

    # 1. 유행 참여 (흥미 정도가 높을수록 참여 확률 증가)
    join_prob = np.clip(
        active_ratio * interest_level,
        0.0,
        1.0
    )

    if active_count > 0 and len(unexposed_indices) > 0:

        random_values = np.random.random(
            len(unexposed_indices)
        )

        new_adopters = unexposed_indices[
            random_values < join_prob
        ]

    else:
        new_adopters = np.array([], dtype=int)

    # 2. 기존 사용자의 흥미 감소
    remaining[active_indices] -= 1

    # 3. 만족 발생 (만족도가 높을수록 확률과 연장 턴 증가)
    if active_count > 0:

        random_values = np.random.random(active_count)

        satisfied_indices = active_indices[
            random_values < satisfaction_prob
        ]

        remaining[satisfied_indices] += satisfaction_extension

    # 4. 흥미 지속 턴이 끝난 사용자는 폐기 (폐기된 사용자는 다시 참여하지 않음)
    expired_indices = active_indices[
        remaining[active_indices] <= 0
    ]

    states[expired_indices] = 2
    remaining[expired_indices] = 0

    # 5. 신규 사용자 등록
    states[new_adopters] = 1
    remaining[new_adopters] = interest_duration

    # 6. 상태 저장
    st.session_state.states = states
    st.session_state.remaining = remaining

    # 7. 턴 증가
    st.session_
