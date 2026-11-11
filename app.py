
def advance_turn():

    # 시뮬레이션 종료 확인
    if st.session_state.turn >= max_turns:
        st.session_state.running = False
        return

    # 상태 배열 가져오기
    states = st.session_state.states
    remaining = st.session_state.remaining

    # 배열 자료형 통일
    states = np.asarray(states, dtype=int)
    remaining = np.asarray(remaining, dtype=int)

    # 참여자 수 확인
    active_indices = np.where(states == 1)[0]
    unexposed_indices = np.where(states == 0)[0]
    dropped_indices = np.where(states == 2)[0]

    active_count = len(active_indices)
    active_ratio = active_count / N if N > 0 else 0

    # --------------------------------------------------
    # 1. 신규 참여 확률
    # --------------------------------------------------

    contact_prob = np.clip(
        active_ratio * infection_prob,
        0.0,
        1.0
    )

    if len(unexposed_indices) > 0 and active_count > 0:

        random_values = np.random.random(
            len(unexposed_indices)
        )

        new_adopters = unexposed_indices[
            random_values < contact_prob
        ]

    else:
        new_adopters = np.array([], dtype=int)

    # --------------------------------------------------
    # 2. 기존 참여자의 흥미 감소
    # --------------------------------------------------

    remaining[active_indices] -= 1

    expired_indices = active_indices[
        remaining[active_indices] <= 0
    ]

    # 흥미가 끝나면 이탈
    states[expired_indices] = 2
    remaining[expired_indices] = 0

    # --------------------------------------------------
    # 3. 신규 참여자 등록
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 4. 이탈자의 재참여
    # --------------------------------------------------

    return_prob = np.clip(
        satisfaction_weight * 0.25,
        0.0,
        1.0
    )

    # 이번 턴에 이탈한 사람도 재참여 대상에 포함
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

    # --------------------------------------------------
    # 5. 상태 저장
    # --------------------------------------------------

    st.session_state.states = states
    st.session_state.remaining = remaining

    # --------------------------------------------------
    # 6. 턴 증가 및 기록
    # --------------------------------------------------

    st.session_state.turn += 1

    st.session_state.history.append({
        "턴": st.session_state.turn,
        "미체험자": int(np.sum(states == 0)),
        "참여 중": int(np.sum(states == 1)),
        "이탈자": int(np.sum(states == 2))
    })

    # 최대 턴 도달 시 종료
    if st.session_state.turn >= max_turns:
        st.session_state.running = False
