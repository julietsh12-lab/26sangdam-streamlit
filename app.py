if st.session_state.user is None:
    st.title("🏫 해운대중학교 진학상담 시스템")
    tab1, tab2 = st.tabs(["로그인", "회원가입"])

    with tab1:
        email = st.text_input("이메일", key="login_email")
        password = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인"):
            if login(email, password):
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("이메일 또는 비밀번호가 틀렸습니다.")

    with tab2:
        new_email = st.text_input("이메일", key="signup_email")
        new_password = st.text_input("비밀번호", type="password", key="signup_pw")
        new_password2 = st.text_input("비밀번호 확인", type="password", key="signup_pw2")
        if st.button("회원가입"):
            if new_password != new_password2:
                st.error("비밀번호가 일치하지 않습니다.")
            elif len(new_password) < 6:
                st.error("비밀번호는 6자 이상이어야 합니다.")
            else:
                try:
                    res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    st.success("회원가입 완료! 로그인 탭에서 로그인해주세요.")
                except:
                    st.error("회원가입 실패. 이미 사용중인 이메일입니다.")
    st.stop()
