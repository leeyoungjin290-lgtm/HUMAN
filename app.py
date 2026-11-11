
def advance_turn():

    if st.session_state.turn >= max_turns:
        st.session_state.running = False
        return

    states = st.session_state.states
    remaining = st.session_state.remaining

    # 현재 상태별 사용자 확인
    active_indices = np.where(states == 1)[0]
    unexposed_indices = np.where(states == 0)[0]
    dropped_indices = np.where(states == 2)[0]

    active_count = len(active_indices)

    active_ratio = active_count / N

    # -----------------------------------------------------
    # ① 미체험자의 신규 참여
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

    # 흥미가 끝난 사용자는 이탈
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
    # ④ 이탈자의 재참여
    # -----------------------------------------------------

    # 만족도가 높을수록 재참여 확률 증가
    return_prob = min(
        1.0,
        satisfaction_weight * 0.25
    )

    # 현재 이탈한 사용자에게 재참여 기회 부여
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

    # 재참여자도 다시 참여 상태로 변경
    states[returning_users] = 1

    # 재참여자의 흥미 지속 시간
    remaining[returning_users] = (
        base_duration + dynamic_bonus
    )

    # -----------------------------------------------------
    # ⑤ 턴 증가 및 기록
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
