
def advance_turn():

    if st.session_state.turn >= max_turns:
        st.session_state.running = False
        return

    states = st.session_state.states
    remaining = st.session_state.remaining

    # 남은 시간 배열을 정수형으로 통일
    remaining = np.asarray(remaining, dtype=int)

    # 현재 참여자 확인
    active_indices = np.where(states == 1)[0]
    unexposed_indices = np.where(states == 0)[0]

    active_count = len(active_indices)
    active_ratio = active_count / N

    # 확률이 0~1 범위를 벗어나지 않도록 제한
    contact_prob = np.clip(
        active_ratio * infection_prob, 0.0, 1.0
    )

    # -----------------------------------------------------
    # ① 미체험자의 신규 참여
    # -----------------------------------------------------

    if active_count > 0 and len(unexposed_indices) > 0:

        random_values = np.random.random(len(unexposed_indices))

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
    remaining[expired_indices] = 0

    # -----------------------------------------------------
    # ③ 신규 참여자 등록
    # -----------------------------------------------------

    dynamic_bonus = (
        base_duration
        * satisfaction_weight
        * active_ratio
    )

    new_duration = max(
        1, int(round(base_duration + dynamic_bonus))
    )

    states[new_adopters] = 1
    remaining[new_adopters] = new_duration

    # -----------------------------------------------------
    # ④ 이탈자의 재참여
    # -----------------------------------------------------

    return_prob = np.clip(
        satisfaction_weight * 0.25, 0.0, 1.0
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

    # 재참여 처리
    states[returning_users] = 1

    remaining[returning_users] = new_duration

    # -----------------------------------------------------
    # ⑤ 상태 저장
    # -----------------------------------------------------

    st.session_state.states = states
    st.session_state.remaining = remaining

    # -----------------------------------------------------
    # ⑥ 턴 증가 및 기록
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
