import time

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

# 전체 실행 시 턴 사이 대기 시간 (고정값)
STEP_DELAY = 0.1

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

satisfaction_base_prob = st.sidebar.slider(
    "만족 발생 기본 확률 (매 턴)", 0.0, 0.5, 0.1, 0.01
)

satisfaction_extension = st.sidebar.slider(
    "만족 발생 시 흥미 지속 연장 턴", 1, 30, 5
)

return_rate = st.sidebar.slider(
    "재참여 기본 확률 (매 턴)", 0.0, 0.3, 0.03, 0.01
)

return_duration_ratio = st.sidebar.slider(
    "재참여 시 흥미 지속 비율", 0.1, 1.0, 0.3, 0.05
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
    float(satisfaction_weight),
    float(satisfaction_base_prob),
    int(satisfaction_extension),
    float(return_rate),
    float(return_duration_ratio)
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

    # 이번 턴 이전부터 이탈해 있던 사람만 재참여 후보
    previously_dropped = np.where(states == 2)[0]

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

    # 3. 만족도 계수에 의한 흥미 지속 연장
    #    흥미 지속 턴 동안 확률적으로 만족이 발생하면 지속 턴이 늘어남
    satisfaction_prob = np.clip(
        satisfaction_weight * satisfaction_base_prob,
        0.0,
        1.0
    )

    if active_count > 0:

        random_values = np.random.random(active_count)

        satisfied_indices = active_indices[
            random_values < satisfaction_prob
        ]

        remaining[satisfied_indices] += satisfaction_extension

    # 4. 흥미 지속 턴이 끝난 참여자는 이탈
    #    (지속 턴 안에 만족이 발생하지 않았다면 여기서 이탈)
    expired_indices = active_indices[
        remaining[active_indices] <= 0
    ]

    states[expired_indices] = 2
    remaining[expired_indices] = 0

    # 5. 신규 참여자 등록
    states[new_adopters] = 1
    remaining[new_adopters] = base_duration

    # 6. 이탈자의 재참여
    return_prob = np.clip(
        satisfaction_weight * return_rate,
        0.0,
        1.0
    )

    if len(previously_dropped) > 0:

        random_values = np.random.random(
            len(previously_dropped)
        )

        returning_users = previously_dropped[
            random_values < return_prob
        ]

    else:
        returning_users = np.array([], dtype=int)

    return_duration = max(
        1,
        int(round(base_duration * return_duration_ratio))
    )

    states[returning_users] = 1
    remaining[returning_users] = return_duration

    # 7. 상태 저장
    st.session_state.states = states
    st.session_state.remaining = remaining

    # 8. 턴 증가
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
# 화면 표시 함수
# --------------------------------------------------

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


def render_all():

    states = st.session_state.states

    st.subheader(
        f"현재 턴: {st.session_state.turn} / {max_turns}"
    )

    if st.session_state.running:
        st.success("시뮬레이션 진행 가능")
    else:
        st.info("시뮬레이션 종료")

    c1, c2, c3 = st.columns(3)
    c1.metric("미체험자", int(np.sum(states == 0)))
    c2.metric("참여 중", int(np.sum(states == 1)))
    c3.metric("이탈자", int(np.sum(states == 2)))

    # 시뮬레이션 보드
    st.divider()
    st.subheader("참여자 상태 시뮬레이션")

    columns = 10

    for start in range(0, len(states), columns):

        cols = st.columns(columns)

        for j, state in enumerate(states[start:start + columns]):

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
                        {start + j + 1}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.caption(labels[int(state)])

    # 범례
    st.markdown(
        """
        🔘 회색: 미체험자

        🔵 파란색: 참여 중

        🔴 빨간색: 이탈자
        """
    )

    # 변화 그래프
    st.divider()
    st.subheader("참여자 수 변화")

    history_df = pd.DataFrame(
        st.session_state.history
    ).set_index("턴")

    st.line_chart(history_df)


# --------------------------------------------------
# 실행 버튼
# --------------------------------------------------

st.divider()

col1, col2, col3 = st.columns(3)

run_all = False

with col1:
    if st.button("▶ 한 턴 진행", use_container_width=True):
        advance_turn()

with col2:
    if st.button("⏩ 전체 실행", use_container_width=True):
        run_all = True

with col3:
    if st.button("🔄 초기화", use_container_width=True):
        reset_simulation()

# --------------------------------------------------
# 화면 출력 (전체 실행 시 턴마다 갱신)
# --------------------------------------------------

placeholder = st.empty()

if run_all:
    while st.session_state.running:
        advance_turn()
        with placeholder.container():
            render_all()
        time.sleep(STEP_DELAY)

with placeholder.container():
    render_all()

# --------------------------------------------------
# 참여자 상세 정보 (맨 아래에 한 번만 표시)
# --------------------------------------------------

with st.expander("참여자별 상세 정보"):

    detail_df = pd.DataFrame({
        "참여자": np.arange(1, int(N) + 1),
        "상태": [labels[int(x)] for x in st.session_state.states],
        "남은 흥미 지속 턴": st.session_state.remaining
    })

    st.dataframe(
        detail_df,
        use_container_width=True,
        hide_index=True
    )
