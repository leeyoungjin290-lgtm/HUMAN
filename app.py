import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. 페이지 설정 및 제목
# ---------------------------------------------------------
st.set_page_config(page_title="신상품 유행 확산 시뮬레이터", layout="wide")

st.title("📉 신상품 유행 확산 및 지속성 분석 시뮬레이터")
st.caption("초기 전파 확률과 실용성 만족도(동적 흥미 지속 효과)에 따른 유행 변화 양상 분석")

# ---------------------------------------------------------
# 2. 사이드바: 변인 설정 (실험 조건 설정)
# ---------------------------------------------------------
st.sidebar.header("⚙️ 실험 변인 설정")

# [고정 조건]
st.sidebar.subheader("📌 고정 조건")
total_agents = st.sidebar.number_input("전체 잠재 소비자 수 (N)", value=100, step=10, disabled=True)
max_turns = st.sidebar.slider("최대 진행 턴 수", min_value=30, max_value=200, value=100, step=10)

# [바꿀 조건]
st.sidebar.subheader("🎛️ 조절 가능한 변인")

# 1) 기본 흥미 지속 시간
base_duration = st.sidebar.slider(
    "기본 흥미 지속 시간 (턴)",
    min_value=1, max_value=50, value=15,
    help="상품을 처음 체험했을 때 유지되는 기본 기간"
)

# 2) 전파 확률 (입소문 및 광고)
infection_prob = st.sidebar.slider(
    "초기 전파 확률 (%)",
    min_value=5, max_value=100, value=50, step=5,
    help="미체험자가 기존 참여자와 상호작용할 때 상품을 구매/체험할 확률"
) / 100.0

# 3) 실용성/만족도 동적 가중치
satisfaction_weight = st.sidebar.slider(
    "실용성/만족도 가중치 (동적 보너스)",
    min_value=0.0, max_value=2.0, value=0.5, step=0.1,
    help="현재 유행 참여율이 높을 때 흥미 지속 시간이 추가로 연장되는 비율"
)

initial_adopters = st.sidebar.slider("초기 얼리어답터 수", min_value=1, max_value=20, value=5)

# ---------------------------------------------------------
# 3. 시뮬레이션 엔진 함수
# ---------------------------------------------------------
def run_simulation(N, max_t, base_dur, p_infect, weight, init_adopters):
    """
    상태 정의:
    0: 미체험자 (Unexposed)
    1: 참여 중 (Active User)
    2: 흥미 종료 / 이탈 (Dropped Out)
    """
    states = np.zeros(N, dtype=int)
    # 초기 얼리어답터 설정
    states[:init_adopters] = 1
    
    # 각 사용자의 남은 흥미 지속 턴 수
    remaining_turns = np.zeros(N)
    remaining_turns[:init_adopters] = base_dur

    # 턴별 기록용 리스트
    history_unexposed = []
    history_active = []
    history_dropped = []

    for t in range(max_t):
        current_active_count = np.sum(states == 1)
        current_unexposed_count = np.sum(states == 0)
        current_dropped_count = np.sum(states == 2)

        history_unexposed.append(current_unexposed_count)
        history_active.append(current_active_count)
        history_dropped.append(current_dropped_count)

        # 1) 전파 단계 (입소문/상호작용 효과)
        # 전체 인원 대비 현재 참여자의 비율을 바탕으로 미체험자와의 접촉 확률 계산
        if current_active_count > 0 and current_unexposed_count > 0:
            active_ratio = current_active_count / N
            # 미체험자 각각에 대해 접촉 및 전파 여부 판정
            unexposed_indices = np.where(states == 0)[0]
            # 참여자 비율에 비례하여 접촉 성공 확률 설정
            contact_prob = active_ratio * p_infect
            new_adopters = np.random.rand(len(unexposed_indices)) < contact_prob
            
            # 신규 참여자 상태 업데이트
            for idx, is_adopted in zip(unexposed_indices, new_adopters):
                if is_adopted:
                    states[idx] = 1
                    # 동적 보너스: 현재 유행 참여율이 높을수록 실용성/만족도 효과로 지속 시간 연장
                    dynamic_bonus = base_dur * weight * active_ratio
                    remaining_turns[idx] = base_dur + dynamic_bonus

        # 2) 지속 시간 감소 및 이탈 처리
        active_indices = np.where(states == 1)[0]
        for idx in active_indices:
            remaining_turns[idx] -= 1
            if remaining_turns[idx] <= 0:
                states[idx] = 2  # 흥미 종료(이탈)

    df_result = pd.DataFrame({
        "Turn": np.arange(max_t),
        "미체험자": history_unexposed,
        "참여 중 (유행 사용자)": history_active,
        "흥미 종료 (이탈)": history_dropped
    })
    
    return df_result

# ---------------------------------------------------------
# 4. 시뮬레이션 실행 및 결과 시각화
# ---------------------------------------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📋 탐구 목적 및 요약")
    st.markdown("""
    - **단기 유행 상품**: 초기 전파율은 높으나 만족도 가중치가 낮아 금방 이탈함.
    - **장기 필수품**: 초기 전파율과 실용성 만족도 가중치가 균형을 이루어 유행이 진정된 후에도 일정 사용자가 계속 유지됨.
    """)
    
    run_button = st.button("🚀 시뮬레이션 실행", type="primary")

# 실행 버튼 눌렀을 때 처리
if run_button or "df_result" not in st.session_state:
    st.session_state.df_result = run_simulation(
        N=total_agents,
        max_t=max_turns,
        base_dur=base_duration,
        p_infect=infection_prob,
        weight=satisfaction_weight,
        init_adopters=initial_adopters
    )

df_res = st.session_state.df_result

with col2:
    st.subheader("📊 턴에 따른 사용자 상태 변화 그래프")
    
    # Matplotlib을 이용한 대시보드 그래프
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_res["Turn"], df_res["참여 중 (유행 사용자)"], label="참여 중 (유행 사용자)", color="#FF4B4B", linewidth=2.5)
    ax.plot(df_res["Turn"], df_res["미체험자"], label="미체험자", color="#808080", linestyle="--")
    ax.plot(df_res["Turn"], df_res["흥미 종료 (이탈)"], label="흥미 종료 (이탈)", color="#1E88E5", linestyle="-.")
    
    ax.set_xlabel("턴 (Time Turn)")
    ax.set_ylabel("인원 수 (명)")
    ax.set_title("Product Adoption Lifecycle Simulation")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="right")
    
    st.pyplot(fig)

# ---------------------------------------------------------
# 5. 수치 요약 및 결론 분석
# ---------------------------------------------------------
st.divider()
st.subheader("📌 핵심 분석 결과")

peak_active = df_res["참여 중 (유행 사용자)"].max()
peak_turn = df_res.loc[df_res["참여 중 (유행 사용자)"] == peak_active, "Turn"].values[0]
final_active = df_res["참여 중 (유행 사용자)"].iloc[-1]
final_dropped = df_res["흥미 종료 (이탈)"].iloc[-1]
retention_rate = (final_active / total_agents) * 100

m1, m2, m3, m4 = st.columns(4)
m1.metric("최대 유행 사용자 수", f"{peak_active} 명", f"턴 {peak_turn} 시점")
m2.metric("최종 남아있는 사용자 수", f"{final_active} 명")
m3.metric("총 이탈자 수", f"{final_dropped} 명")
m4.metric("최종 정착률 (필수품화)", f"{retention_rate:.1f} %")

st.markdown("### 💡 분석 가이드")
if retention_rate < 10 and peak_active > 40:
    st.warning("⚠️ **전형적인 단기 반짝 유행 상품 패턴입니다.** 초기 홍보/입소문 효과로 peaks는 높았으나, 실용성/지속성이 부족하여 빠르게 이탈했습니다.")
elif retention_rate >= 30:
    st.success("✅ **장기 필수품으로 정착한 패턴입니다.** 높거나 안정적인 실용성 보너스로 인해 사용자가 지속적으로 유지되고 있습니다.")
else:
    st.info("ℹ️ **중립적 유행 완화 패턴입니다.** 전파력과 지속성을 추가 조정하며 정착 지점을 탐색해 보세요.")

st.dataframe(df_res.tail(10), use_container_state_grid=True)
