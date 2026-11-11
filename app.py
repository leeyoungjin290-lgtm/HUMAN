
import streamlit as st
import numpy as np
import pandas as pd
import html

# ---------------------------------------------------------
# 1. 페이지 설정
# ---------------------------------------------------------

st.set_page_config(
    page_title="신상품 유행 확산 시뮬레이터",
    page_icon="📊",
    layout="wide"
)

st.title("📊 신상품 유행 확산 및 지속성 시뮬레이터")
st.caption("100명의 소비자가 신상품을 체험하고 유행이 확산되거나 사라지는 과정을 관찰합니다.")

# ---------------------------------------------------------
# 2. 색상 및 상태 설정
# ---------------------------------------------------------

COLORS = {
    0: "#858585",  # 미체험자
    1: "#FF4B4B",  # 참여 중
    2: "#2878D0"   # 이탈자
}

STATE_NAMES = {
    0: "미체험자",
    1: "참여 중",
    2: "흥미 종료"
}

N = 100

# ---------------------------------------------------------
# 3. 사이드바 설정
# ---------------------------------------------------------

st.sidebar.header("⚙️ 실험 변인 설정")

st.sidebar.subheader("📌 고정 조건")

st.sidebar.number_input(
    "전체 소비자 수",
    value=100,
    disabled=True
)

max_turns = st.sidebar.slider(
    "최대 진행 턴",
    30, 200, 100, 10
)

st.sidebar.subheader("🎛️ 조절 가능한 변인")

base_duration = st.sidebar.slider(
    "기본 흥미 지속 시간",
    1, 50, 15
)

infection_prob = st.sidebar.slider(
    "초기 전파 확률 (%)",
    5, 100, 50, 5
) / 100

satisfaction_weight = st.sidebar.slider(
    "실용성/만족도 가중치",
    0.0, 2.0, 0.5, 0.1
)

initial_adopters = st.sidebar.slider(
    "초기 얼리어답터 수",
    1, 20, 5
)

# ---------------------------------------------------------
# 4. 시뮬레이션 초기화
# ---------------------------------------------------------

def reset_simulation():

    states = np.zeros(N, dtype=int)

    # 초기 사용자를 무작위 위치에 배치
    initial_indices = np.random.choice(
        N,
        initial_adopters,
        replace=False
    )

    states[initial_indices] = 1

    remaining = np.zeros(N, dtype=float)
    remaining[initial_indices] = base_duration

    st.session_state.states = states
    st.session_state.remaining = remaining
    st.session_state.turn = 0
    st.session_state.running = False

    st.session_state.history = [{
        "턴": 0,
        "미체험자": int(np.sum(states == 0)),
        "참여 중": int(np.sum(states == 1)),
        "이탈자": int(np.sum(states == 2))
    }]


# ---------------------------------------------------------
# 5. 한 턴 진행 함수
# ---------------------------------------------------------

def advance_turn():

    states = st.session_state.states
    remaining = st.session_state.remaining

    if st.session_state.turn >= max_turns:
        st.session_state.running = False
        return

    # 현재 상태 확인
    active_indices = np.where(states == 1)[0]
    unexposed_indices = np.where(states == 0)[0]

    active_count = len(active_indices)

    active_ratio = active_count / N

    # 기존 참여자는 이번 턴에 흥미 지속 시간이 감소
    remaining[active_indices] -= 1

    # 흥미가 끝난 사람은 이탈
    expired_indices = active_indices[
        remaining[active_indices] <= 0
    ]

    states[expired_indices] = 2

    # -----------------------------------------------------
    # 입소문을 통한 신규 사용자 발생
    # -----------------------------------------------------

    contact_prob = active_ratio * infection_prob

    if len(unexposed_indices) > 0 and active_count > 0:

        random_values = np.random.random(
            len(unexposed_indices)
        )

        adopted = unexposed_indices[
            random_values < contact_prob
        ]

        # 신규 참여자 상태 변경
        states[adopted] = 1

        # 만족도에 따른 지속 시간 보너스
        dynamic_bonus = (
            base_duration
            * satisfaction_weight
            * active_ratio
        )

        remaining[adopted] = (
            base_duration + dynamic_bonus
        )

    # -----------------------------------------------------
    # 턴 기록
    # -----------------------------------------------------

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
# 6. 설정 변경 감지 및 초기화
# ---------------------------------------------------------

current_config = (
    max_turns,
    base_duration,
    infection_prob,
    satisfaction_weight,
    initial_adopters
)

if (
    "config" not in st.session_state
    or st.session_state.config != current_config
):
    st.session_state.config = current_config
    reset_simulation()


# ---------------------------------------------------------
# 7. 바둑판 생성 함수
# ---------------------------------------------------------

def draw_board():

    states = st.session_state.states

    cells = []

    for i, state in enumerate(states):

        color = COLORS[int(state)]
        name = STATE_NAMES[int(state)]

        cells.append(
            f"""
            <div
                title="{i+1}번 소비자: {name}"
                style="
                    background-color: {color};
                    aspect-ratio: 1;
                    border-radius: 5px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    border: 1px solid rgba(255,255,255,0.2);
                "
            >
                {i+1}
            </div>
            """
        )

    board_html = f"""
    <div style="
        display: grid;
        grid-template-columns: repeat(10, minmax(0, 1fr));
        gap: 5px;
        width: 100%;
    ">
        {''.join(cells)}
    </div>
    """

    st.markdown(board_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 8. 시뮬레이션 화면
# ---------------------------------------------------------

st.subheader("🟩 소비자 상태 시뮬레이션")

# 범례
legend1, legend2, legend3 = st.columns(3)

legend1.markdown(
    "⬜ **미체험자**"
)

legend2.markdown(
    "🟥 **참여 중**"
)

legend3.markdown(
    "🟦 **흥미 종료 / 이탈**"
)

# 자동 실행과 화면 갱신
@st.fragment(run_every=0.5)
def simulation_panel():

    # 실행 버튼
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("▶ 시작 / 재개", use_container_width=True):
            if st.session_state.turn < max_turns:
                st.session_state.running = True

    with c2:
        if st.button("⏸ 일시정지", use_container_width=True):
            st.session_state.running = False

    with c3:
        if st.button("⏭ 다음 턴", use_container_width=True):
            st.session_state.running = False
            advance_turn()

    with c4:
        if st.button("🔄 초기화", use_container_width=True):
            reset_simulation()

    # 자동 실행
    if st.session_state.running:
        advance_turn()

    # 현재 턴 표시
    st.markdown(
        f"### 현재 진행: {st.session_state.turn} / {max_turns} 턴"
    )

    # 진행률
    st.progress(
        min(st.session_state.turn / max_turns, 1.0)
    )

    # 바둑판 출력
    draw_board()

    # 현재 사용자 수
    states = st.session_state.states

    active = int(np.sum(states == 1))
    unexposed = int(np.sum(states == 0))
    dropped = int(np.sum(states == 2))

    st.divider()

    m1, m2, m3 = st.columns(3)

    m1.metric("🟥 참여 중", f"{active}명")
    m2.metric("⬜ 미체험자", f"{unexposed}명")
    m3.metric("🟦 이탈자", f"{dropped}명")

    if st.session_state.turn >= max_turns:
        st.success("시뮬레이션이 종료되었습니다.")
    elif st.session_state.running:
        st.info("시뮬레이션 자동 진행 중")
    else:
        st.info("시작 버튼을 눌러 시뮬레이션을 진행하세요.")


simulation_panel()


# ---------------------------------------------------------
# 9. 그래프 및 분석
# ---------------------------------------------------------

st.divider()

st.subheader("📈 턴에 따른 사용자 변화")

df = pd.DataFrame(st.session_state.history)

chart_data = df.set_index("턴")[
    ["미체험자", "참여 중", "이탈자"]
]

st.line_chart(
    chart_data,
    height=350
)

# ---------------------------------------------------------
# 10. 최종 분석
# ---------------------------------------------------------

st.divider()

st.subheader("📌 핵심 분석 결과")

states = st.session_state.states

final_active = int(np.sum(states == 1))
final_dropped = int(np.sum(states == 2))

history_df = pd.DataFrame(st.session_state.history)

peak_active = int(history_df["참여 중"].max())

peak_turn = int(
    history_df.loc[
        history_df["참여 중"].idxmax(),
        "턴"
    ]
)

retention_rate = final_active / N * 100

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "최대 유행 사용자",
    f"{peak_active}명",
    f"{peak_turn}턴"
)

m2.metric(
    "최종 참여자",
    f"{final_active}명"
)

m3.metric(
    "최종 이탈자",
    f"{final_dropped}명"
)

m4.metric(
    "최종 정착률",
    f"{retention_rate:.1f}%"
)

st.subheader("💡 분석")

if retention_rate < 10 and peak_active > 40:

    st.warning(
        "초기에는 빠르게 확산되었지만 "
        "지속성이 부족하여 대부분의 사용자가 이탈한 "
        "단기 유행 상품 패턴입니다."
    )

elif retention_rate >= 30:

    st.success(
        "유행이 진정된 이후에도 상당수 사용자가 남아 있는 "
        "장기 정착 상품 패턴입니다."
    )

else:

    st.info(
        "전파력과 지속성이 복합적으로 작용한 "
        "중간 단계의 유행 패턴입니다."
    )

st.subheader("📋 턴별 상세 데이터")

st.dataframe(
    history_df.tail(20),
    use_container_width=True,
    hide_index=True
)
