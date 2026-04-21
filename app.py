import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

# ─── Supabase 연결 ───────────────────────────────
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ─── 페이지 설정 ──────────────────────────────────
st.set_page_config(page_title="해운대중학교 진학상담", layout="wide")

# ─── 로그인 상태 초기화 ───────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# ─── 로그인 함수 ──────────────────────────────────
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        role_res = supabase.table("user_roles").select("role").eq("user_id", res.user.id).execute()
        if role_res.data:
            st.session_state.role = role_res.data[0]["role"]
        return True
    except:
        return False

# ─── 로그인/회원가입 화면 ─────────────────────────
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

# ─── 로그아웃 및 사이드바 ──────────────────────────
with st.sidebar:
    st.write(f"👤 {st.session_state.user.email}")
    st.write(f"🔑 역할: {st.session_state.role}")
    if st.button("로그아웃"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()
    st.divider()
    menu = st.radio("메뉴", ["학생 목록", "상담 기록 작성", "상담 기록 조회"])

# ─── 학생 목록 ────────────────────────────────────
if menu == "학생 목록":
    st.title("📋 학생 목록")
    try:
        # Supabase에서 데이터 가져오기
        res = supabase.table("student_records").select("*").execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            
            # 학번(예: 30101)의 첫 글자를 따서 '학년' 컬럼 생성
            df['학년'] = df['학번'].astype(str).str[0].astype(int)
            
            # 화면에 보여줄 컬럼 선택 (Supabase의 한글 컬럼명 기준)
            # 필요한 컬럼이 더 있다면 여기에 추가하세요 (예: "희망학교2")
            show_cols = ["학년", "학번", "이름", "희망학교1", "희망직업(본인)"]
            existing_cols = [c for c in show_cols if c in df.columns]
            df_display = df[existing_cols].copy()
            
            # 컬럼 이름 예쁘게 바꾸기
            df_display.columns = ["학년", "학번", "이름", "희망학교", "희망직업"]
            
            # 학년 필터
            grade_filter = st.selectbox("학년 선택", ["전체", 1, 2, 3])
            if grade_filter != "전체":
                df_display = df_display[df_display["학년"] == grade_filter]
            
            st.write(f"총 {len(df_display)}명")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("학생 데이터가 없습니다. Supabase에 데이터를 먼저 넣어주세요.")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")

# ─── 상담 기록 작성 ───────────────────────────────
elif menu == "상담 기록 작성":
    st.title("📝 상담 기록 작성")
    try:
        # 학생 목록 가져오기 (학번과 이름 사용)
        students_res = supabase.table("student_records").select("학번, 이름").execute()
        students = students_res.data or []
        student_options = [f"{s['학번']} {s['이름']}" for s in students]

        selected = st.selectbox("학생 선택", student_options if student_options else ["학생 없음"])
        counsel_date = st.date_input("상담 날짜", value=date.today())
        fields = st.multiselect("상담 분야", ["진학", "진로", "학업"])
        types = st.multiselect("상담 유형", ["학생대면상담", "학부모대면상담", "학생온라인상담", "학부모온라인상담", "학부모유선상담", "담임상담"])
        content = st.text_area("상담 내용", height=200)

        if st.button("저장"):
            if not students:
                st.error("학생 데이터가 없습니다.")
            elif not fields or not types or not content:
                st.error("모든 항목을 입력해주세요.")
            else:
                # 선택된 문자열에서 학번과 이름 분리
                student_id = selected.split(" ")[0]
                student_name = selected.split(" ")[1]
                
                supabase.table("counseling_records").insert({
                    "student_id": student_id,
                    "student_name": student_name,
                    "counseling_date": str(counsel_date),
                    "counseling_field": ", ".join(fields),
                    "counseling_types": types,
                    "counseling_content": content
                }).execute()
                st.success(f"{student_name} 학생 상담 기록이 저장되었습니다!")
    except Exception as e:
        st.error(f"오류: {e}")

# ─── 상담 기록 조회 ───────────────────────────────
elif menu == "상담 기록 조회":
    st.title("🗂️ 상담 기록 조회")
    try:
        res = supabase.table("counseling_records").select("*").order("counseling_date", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df = df[["counseling_date", "student_name", "student_id", "counseling_field", "counseling_content"]]
            df.columns = ["날짜", "이름", "학번", "분야", "내용"]
            search = st.text_input("🔍 학생 이름 검색")
            if search:
                df = df[df["이름"].str.contains(search)]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("상담 기록이 없습니다.")
    except Exception as e:
        st.error(f"오류: {e}")
