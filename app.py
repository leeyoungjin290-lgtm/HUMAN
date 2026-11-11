
import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="참여자 변화 시뮬레이션",
    page_icon="🔲",
    layout="wide"
)

st.title("참여자 변화 시뮬레이션")
st.write("참여자의 확산, 흥미 감소, 이탈 및 재참여를 관찰합니다.")

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
    "초기 참여자 수",
    min_value=1,
    max_value=int(N),
    value=min(5, int(N))
)

max_turns = st.sidebar.slider(
    "최대 턴 수", 10, 200, 50
)

infection_prob = st.sidebar.slider(
    "신규 참여 확률 계수", 0.0, 2.0, 1.0, 0.05
)

base_duration = st.sidebar.slider(
    "기본 흥미 지속 턴", 1, 30, 10
)

satisfaction_weight = st.sidebar.slider(
    "만족도 계수", 0.0, 2.0, 1.0, 0.05
)

# --------------------------------------------------
# 초기화
# --------------------------------------------------

def reset_simulation():

    states = np.zeros(int(N), dtype=int)
    remaining = np.zeros(int(N), dtype=int)

    states[:int(initial_users)] = 1
    remaining[:int(initial_users)] = base_duration

    st.session_state.states = states
    st.session_state.remaining = remaining
    st.session_state.turn = 0
    st.session_state.running = True

    st.session_state.history = [{
        "턴": 0,
        "미체험자": int(np.sum(states == 0)),
        "참여 중": int(np.sum(states == 1)),
        "이탈자": int(np.sum(states == 2))
    }]


# --------------------------------------------------
# 세션 초기화 및 설정 변경 확인
# --------------------------------------------------

settings = (
    int(N),
    int(initial_users),
    int(max_turns),
    float(infection_prob),
    int(base_duration),
    float(satisfaction_weight)
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

    # 턴 시작 시 기존 참여자 확인
    active_indices = np.where(states == 1)[0]
    unexposed_indices = np.where(states == 0)[0]

    active_count = len(active_indices)
    active_ratio = active_count / N

    # 1. 신규 참여 확률
    contact_prob = np.clip(
        active_ratio * infection_prob,
        0.0,
        1.0
    )

    if active_count > 0 and len(unexposed_indices) > 0:

        random_values = np.random.random(
            len(unexposed_indices)
        )

        new_adopters = unexposed_indices[
            random_values < contact_prob
        ]

    else:
        new_adopters = np.array([], dtype=int)

    # 2. 기존 참여자의 흥미 감소
    remaining[active_indices] -= 1

    expired_indices = active_indices[
        remaining[active_indices] <= 0
    ]

    states[expired_indices] = 2
    remaining[expired_indices] = 0

    # 3. 신규 참여자 등록
    dynamic_bonus = (
        base_duration
        * satisfaction_weight
        * active_ratio
    )

    new_duration = max(
        1,
        int(round(base_duration + dynamic_bonus))
    )

    states[new_adopters] = 1
    remaining[new_adopters] = new_duration

    # 4. 이탈자의 재참여
    return_prob = np.clip(
        satisfaction_weight * 0.25,
        0.0,
        1.0
    )

    dropped_indices = np.where(states == 2)[0]

    if len(dropped_indices) > 0:

        random_values = np.random.random(
            len(dropped_indices)
        )

        returning_users = dropped_indices[
            random_values < return_prob
        ]

    else:
        returning_users = np.array([], dtype=int)

    states[returning_users] = 1
    remaining[returning_users] = new_duration

    # 5. 상태 저장
    st.session_state.states = states
    st.session_state.remaining = remaining

    # 6. 턴 증가
    st.session_state.turn += 1

    st.session_state.history.append({
        "턴": st.session_state.turn,
        "미체험자": int(np.sum(states == 0)),
        "참여 중": int(np.sum(states == 1)),
        "이탈자": int(np.sum(states == 2))
    })

    if st.session_state.turn >= max_turns:
        st.session_state.running = False


# --------------------------------------------------
# 실행 버튼
# --------------------------------------------------

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("▶ 한 턴 진행", use_container_width=True):

        advance_turn()

with col2:
    if st.button("⏩ 전체 실행", use_container_width=True):

        while st.session_state.running:
            advance_turn()

with col3:
    if st.button("🔄 초기화", use_container_width=True):

        reset_simulation()

# --------------------------------------------------
# 현재 상태
# --------------------------------------------------

states = st.session_state.states
remaining = st.session_state.remaining

unexposed_count = int(np.sum(states == 0))
active_count = int(np.sum(states == 1))
dropped_count = int(np.sum(states == 2))

st.subheader(
    f"현재 턴: {st.session_state.turn} / {max_turns}"
)

if st.session_state.running:
    st.success("시뮬레이션 진행 가능")
else:
    st.info("시뮬레이션 종료")

c1, c2, c3 = st.columns(3)

c1.metric("미체험자", unexposed_count)
c2.metric("참여 중", active_count)
c3.metric("이탈자", dropped_count)

# --------------------------------------------------
# 시뮬레이션 보드
# --------------------------------------------------

st.divider()
st.subheader("참여자 상태 시뮬레이션")

colors = {
    0: "#BDBDBD",
    1: "#2196F3",
    2: "#EF5350"
}

labels = {
    0: "미체험자",
    1: "참여 중",
    2: "이탈자"
}

# 10열 보드
columns = 10

for start in range(0, len(states), columns):

    row_states = states[start:start + columns]

    cols = st.columns(columns)

    for j, state in enumerate(row_states):

        participant_id = start + j + 1

        with cols[j]:
            st.markdown(
                f"""
                <div style="
                    background:{colors[int(state)]};
                    height:55px;
                    border-radius:6px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    color:white;
                    font-weight:bold;
                    margin-bottom:5px;
                ">
                    {participant_id}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption(labels[int(state)])

# --------------------------------------------------
# 범례
# --------------------------------------------------

st.markdown(
    """
    🔘 회색: 미체험자

    🔵 파란색: 참여 중

    🔴 빨간색: 이탈자
    """
)

# --------------------------------------------------
# 변화 그래프
# --------------------------------------------------

st.divider()
st.subheader("참여자 수 변화")

history_df = pd.DataFrame(
    st.session_state.history
).set_index("턴")

st.line_chart(history_df)

# --------------------------------------------------
# 참여자 상세 정보
# --------------------------------------------------

with st.expander("참여자별 상세 정보"):

    detail_df = pd.DataFrame({
        "참여자": np.arange(1, N + 1),
        "상태": [labels[int(x)] for x in states],
        "남은 흥미 지속 턴": remaining
    })

    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True
    )
