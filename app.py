
import streamlit as st
import numpy as np
import pandas as pd

# =========================================================
# 1. 페이지 설정
# =========================================================

st.set_page_config(
    page_title="신상품 유행 확산 시뮬레이터",
    page_icon="📊",
    layout="wide"
)

st.title("📊 신상품 유행 확산 및 지속성 시뮬레이터")
st.caption("초기 전파 확률과 실용성·만족도에 따른 유행 확산 및 지속성 분석")

N = 100

# =========================================================
# 2. 상태 설정
# =========================================================

COLORS = {
    0: "⬜",  # 미체험자
    1: "🟥",  # 참여 중
    2: "🟦"   # 이탈자
}

STATE_NAMES = {
    0: "미체험자",
    1: "참여 중",
    2: "흥미 종료"
}

# =========================================================
# 3. 사이드바 - 실험 변인
# =========================================================

st.sidebar.header("⚙️ 실험 변인 설정")

st.sidebar.subheader("📌 고정 조건")

st.sidebar.number_input(
    "전체 소비자 수",
    min_value=100,
    max_value=100,
    value=100,
    disabled=True
)

max_turns = st.sidebar.slider(
    "최대 진행 턴",
    min_value=30,
    max_value=200,
    value=100,
    step=10
)

st.sidebar.subheader("🎛️ 조절 가능한 변인")

base_duration = st.sidebar.slider(
    "기본 흥미 지속 시간 (턴)",
    min_value=1,
    max_value=50,
    value=15
)

infection_prob = st.sidebar.slider(
    "초기 전파 확률 (%)",
    min_value=5,
    max_value=100,
    value=50,
    step=5
) / 100

satisfaction_weight = st.sidebar.slider(
    "실용성/만족도 가중치",
    min_value=0.0,
    max_value=2.0,
    value=0.5,
    step=0.1
)

initial_adopters = st.sidebar.slider(
    "초기 얼리어답터 수",
    min_value=1,
    max_value=20,
    value=5
)

# =========================================================
# 4. 시뮬레이션 초기화
# =========================================================

def reset_simulation():

    states = np.zeros(N, dtype=int)

    # 초기 얼리어답터 무작위 배치
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


# =========================================================
# 5. 한 턴 진행
# =========================================================

def advance_turn():

    if st.session_state.turn >= max_turns:
        st.session_state.running = False
        return

    states = st.session_state.states
    remaining = st.session_state.remaining

    # 현재 참여자와 미체험자 확인
    active_indices = np.where(states == 1)[0]
    unexposed_indices = np.where(states == 0)[0]

    active_count = len(active_indices)

    active_ratio = active_count / N

    # -----------------------------------------------------
    # ① 입소문 전파
    # -----------------------------------------------------

    contact_prob = active_ratio * infection_prob

    if active_count > 0 and len(unexposed_indices) > 0:

        random_values = np.random.random(
            len(unexposed_indices)
        )

        new_adopters = unexposed_indices[
            random_values < contact_prob
        ]

    else:
        new_adopters = np.array([], dtype=int)

    # -----------------------------------------------------
    # ② 기존 참여자의 흥미 지속 시간 감소
    # -----------------------------------------------------

    remaining[active_indices] -= 1

    expired_indices = active_indices[
        remaining[active_indices] <= 0
    ]

    states[expired_indices] = 2

    # -----------------------------------------------------
    # ③ 신규 참여자 등록
    # -----------------------------------------------------

    dynamic_bonus = (
        base_duration
        * satisfaction_weight
        * active_ratio
    )

    new_duration = base_duration + dynamic_bonus

    states[new_adopters] = 1
    remaining[new_adopters] = new_duration

    # -----------------------------------------------------
    # ④ 턴 증가 및 기록
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


# =========================================================
# 6. 설정 변경 확인
# =========================================================

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


# =========================================================
# 7. 바둑판 출력
# =========================================================

def draw_board():

    states = st.session_state.states

    for row in range(10):

        columns = st.columns(10, gap="small")

        for col in range(10):

            index = row * 10 + col
            state = int(states[index])

            with columns[col]:

                st.markdown(
                    f"### {COLORS[state]}"
                )

                st.caption(
                    f"{index + 1}"
                )


# =========================================================
# 8. 실시간 시뮬레이션 화면
# =========================================================

st.divider()
st.subheader("🟩 소비자 상태 시뮬레이션")

st.markdown(
    "⬜ 미체험자　　🟥 참여 중　　🟦 흥미 종료 / 이탈"
)

@st.fragment(run_every=0.5)
def simulation_panel():

    # -----------------------------------------------------
    # 실행 버튼
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # 자동 진행
    # -----------------------------------------------------

    if st.session_state.running:
        advance_turn()

    # -----------------------------------------------------
    # 진행 상황
    # -----------------------------------------------------

    current_turn = st.session_state.turn

    st.markdown(
        f"### 현재 진행: {current_turn} / {max_turns} 턴"
    )

    st.progress(
        current_turn / max_turns
    )

    # -----------------------------------------------------
    # 바둑판
    # -----------------------------------------------------

    draw_board()

    # -----------------------------------------------------
    # 현재 사용자 수
    # -----------------------------------------------------

    states = st.session_state.states

    active = int(np.sum(states == 1))
    unexposed = int(np.sum(states == 0))
    dropped = int(np.sum(states == 2))

    st.divider()
    st.subheader("📊 현재 사용자 현황")

    m1, m2, m3 = st.columns(3)

    m1.metric("🟥 참여 중", f"{active}명")
    m2.metric("⬜ 미체험자", f"{unexposed}명")
    m3.metric("🟦 이탈자", f"{dropped}명")

    # -----------------------------------------------------
    # 진행 상태
    # -----------------------------------------------------

    if current_turn >= max_turns:
        st.success("시뮬레이션이 종료되었습니다.")

    elif st.session_state.running:
        st.info("시뮬레이션이 자동으로 진행 중입니다.")

    else:
        st.info("시작 버튼을 눌러 시뮬레이션을 진행하세요.")

    # =====================================================
    # 9. 사용자 변화 그래프
    # =====================================================

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

    # =====================================================
    # 10. 최종 분석
    # =====================================================

    st.divider()
    st.subheader("📌 핵심 분석 결과")

    peak_active = int(df["참여 중"].max())

    peak_turn = int(
        df.loc[
            df["참여 중"].idxmax(),
            "턴"
        ]
    )

    retention_rate = active / N * 100

    a, b, c, d = st.columns(4)

    a.metric(
        "최대 유행 사용자",
        f"{peak_active}명",
        f"{peak_turn}턴"
    )

    b.metric(
        "최종 참여자",
        f"{active}명"
    )

    c.metric(
        "최종 이탈자",
        f"{dropped}명"
    )

    d.metric(
        "최종 정착률",
        f"{retention_rate:.1f}%"
    )

    # -----------------------------------------------------
    # 분석 문구
    # -----------------------------------------------------

    st.subheader("💡 분석")

    if retention_rate < 10 and peak_active > 40:

        st.warning(
            "초기에는 빠르게 확산되었지만 "
            "지속성이 부족하여 대부분 이탈한 "
            "단기 유행 상품 패턴입니다."
        )

    elif retention_rate >= 30:

        st.success(
            "유행이 진정된 이후에도 사용자가 남아 있는 "
            "장기 정착 상품 패턴입니다."
        )

    else:

        st.info(
            "전파력과 지속성이 복합적으로 작용한 "
            "중간 단계의 유행 패턴입니다."
        )

    # -----------------------------------------------------
    # 상세 데이터
    # -----------------------------------------------------

    st.subheader("📋 턴별 상세 데이터")

    st.dataframe(
        df.tail(20),
        use_container_width=True,
        hide_index=True
    )


simulation_panel()
