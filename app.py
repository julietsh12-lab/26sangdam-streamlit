import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

# ─── Supabase 연결 ───────────────────────────────
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ─── 페이지 설정 ──────────────────────────────────
st.set_page_config(page_title="해운대중학교 진학상담", layout="centered")

# ─── 커스텀 CSS (UI 스타일 유지) ──────────────────
st.markdown("""
<style>
    .school-title {
        color: #1e3a8a;
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 10px;
    }
    .sub-title {
        color: #64748b;
        font-size: 16px;
        text-align: center;
        margin-bottom: 30px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1e3a8a;
        color: white;
        height: 45px;
        font-weight: bold;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

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

# ─── 메인 화면 로직 ─────────────────────────────
if st.session_state.user is None:
    st.markdown('<div class="school-title">🏫 해운대중학교</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">진학상담 시스템 로그인을 환영합니다.</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
    with tab1:
        email = st.text_input("이메일 주소", placeholder="example@email.com", key="login_email")
        password = st.text_input("비밀번호", type="password", key="login_pw")
        if st.button("로그인"):
            if login(email, password):
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("로그인 정보를 확인해주세요.")
    with tab2:
        new_email = st.text_input("사용할 이메일", key="signup_email")
        new_pw = st.text_input("비밀번호 (6자 이상)", type="password", key="signup_pw")
        if st.button("회원가입 완료"):
            try:
                supabase.auth.sign_up({"email": new_email, "password": new_pw})
                st.success("가입 완료! 로그인 탭을 이용해 주세요.")
            except: st.error("가입 실패")
    st.stop()

# ─── 로그인 후 화면 ──────────────────────────────
else:
    with st.sidebar:
        st.markdown(f"### 👤 안녕하세요")
        if st.session_state.role == "admin":
            st.info(f"{st.session_state.user.email}\n\n**역할:** {st.session_state.role}")
        else:
            st.success(f"{st.session_state.user.email}")
            
        if st.button("로그아웃"):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
        st.divider()
        menu = st.radio("📋 메뉴 선택", ["🏠 학생 목록", "✍️ 상담 기록 작성", "🔍 상담 기록 조회"])

    if menu == "🏠 학생 목록":
        st.title("🏠 학생 목록")
        try:
            res = supabase.table("student_records").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                
                # 💡 희망학교 1, 2, 3지망을 모두 선택하도록 수정
                cols = ["학번", "이름", "희망학교1", "희망학교2", "희망학교3", "희망직업(본인)"]
                
                # 데이터베이스에 실제 존재하는 컬럼만 가져오기 (에러 방지)
                existing_cols = [c for c in cols if c in df.columns]
                df_display = df[existing_cols].copy()
                
                # 표 헤더 이름을 알기 쉽게 변경
                # 지망 학교가 3개 다 있는 경우에만 이름을 변경합니다.
                rename_dict = {
                    "학번": "학번",
                    "이름": "이름",
                    "희망학교1": "1지망",
                    "희망학교2": "2지망",
                    "희망학교3": "3지망",
                    "희망직업(본인)": "희망직업"
                }
                df_display.rename(columns=rename_dict, inplace=True)
                
                st.write(f"총 {len(df_display)}명 (3학년)")
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else: 
                st.info("학생 데이터가 없습니다.")
        except Exception as e: 
            st.error(f"오류: {e}")

    elif menu == "✍️ 상담 기록 작성":
        st.title("✍️ 상담 기록 작성")
        try:
            s_res = supabase.table("student_records").select("학번, 이름").execute()
            s_list = [f"{s['학번']} {s['이름']}" for s in s_res.data]
            
            selected_s = st.selectbox("학생 선택", s_list)
            c_date = st.date_input("상담 일자", value=date.today())
            content = st.text_area("상담 상세 내용", height=300)
            
            if st.button("상담 기록 저장"):
                sid, sname = selected_s.split(" ")
                supabase.table("counseling_records").insert({
                    "student_id": sid,
                    "student_name": sname,
                    "counseling_date": str(c_date),
                    "counseling_content": content
                }).execute()
                st.success(f"{sname} 학생의 상담 기록이 저장되었습니다.")
        except Exception as e: st.error(f"오류: {e}")

    elif menu == "🔍 상담 기록 조회":
        st.title("🔍 상담 기록 조회")
        try:
            res = supabase.table("counseling_records").select("*").order("counseling_date", desc=True).execute()
            if res.data:
                df = pd.DataFrame(res.data)
                search = st.text_input("🔍 학생 이름으로 검색")
                if search:
                    df = df[df["student_name"].str.contains(search)]
                
                for _, row in df.iterrows():
                    with st.expander(f"📅 {row['counseling_date']} | {row['student_name']} ({row['student_id']})"):
                        st.info(row['counseling_content'])
            else: st.info("기록이 없습니다.")
        except Exception as e: st.error(f"오류: {e}")
