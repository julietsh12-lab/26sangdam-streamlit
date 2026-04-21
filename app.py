import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

# ─── Supabase 연결 ───────────────────────────────
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# ─── 페이지 설정 ──────────────────────────────────
st.set_page_config(page_title="해운대중학교 진학상담", layout="centered") # 로그인 화면을 위해 centered로 시작

# ─── 커스텀 CSS (이미지 느낌 살리기) ────────────────
st.markdown("""
<style>
    /* 배경색 및 폰트 */
    .main {
        background-color: #f8f9fa;
    }
    
    /* 로그인 박스 스타일 */
    .login-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-top: 50px;
    }
    
    /* 제목 스타일 */
    .school-title {
        color: #1e3a8a; /* 학교 상징 남색 */
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
    
    /* 버튼 스타일 커스텀 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1e3a8a;
        color: white;
        height: 45px;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #3b82f6;
        color: white;
    }

    /* 입력창 라벨 숨기기 (이미지처럼 깔끔하게) */
    .stTextInput>label {
        font-weight: 600;
        color: #475569;
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
    # --- 로그인 화면 UI ---
    st.markdown('<div class="school-title">🏫 해운대중학교</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">진학상담 시스템 로그인을 환영합니다.</div>', unsafe_allow_html=True)
    
    with st.container():
        tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
        
        with tab1:
            email = st.text_input("이메일 주소", placeholder="example@email.com", key="login_email")
            password = st.text_input("비밀번호", type="password", placeholder="Password", key="login_pw")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("로그인"):
                if login(email, password):
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("이메일 또는 비밀번호를 확인해주세요.")
        
        with tab2:
            new_email = st.text_input("사용할 이메일", placeholder="new_user@email.com", key="signup_email")
            new_pw = st.text_input("비밀번호 (6자 이상)", type="password", key="signup_pw")
            new_pw2 = st.text_input("비밀번호 확인", type="password", key="signup_pw2")
            if st.button("회원가입 완료"):
                if new_pw != new_pw2: st.error("비밀번호가 일치하지 않습니다.")
                elif len(new_pw) < 6: st.error("비밀번호를 6자 이상 입력해주세요.")
                else:
                    try:
                        supabase.auth.sign_up({"email": new_email, "password": new_pw})
                        st.success("가입 완료! 로그인 탭에서 이용해주세요.")
                    except: st.error("가입 실패 (이미 사용 중인 이메일)")

else:
    # --- 로그인 성공 후 대시보드 ---
    # 로그인 후에는 넓은 화면 사용
    # st.set_page_config(layout="wide") # 이미 호출되어 변경 불가할 경우 대비 sidebar 활용
    
    with st.sidebar:
        st.markdown(f"### 👤 안녕하세요")
        st.info(f"{st.session_state.user.email}\n\n**역할:** {st.session_state.role}")
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
                df['학년'] = df['학번'].astype(str).str[0]
                df_display = df[["학년", "학번", "이름", "희망학교1", "희망직업(본인)"]]
                df_display.columns = ["학년", "학번", "이름", "희망학교", "희망직업"]
                
                grade = st.selectbox("학년 필터", ["전체", "1", "2", "3"])
                if grade != "전체":
                    df_display = df_display[df_display["학년"] == grade]
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else: st.info("학생 데이터가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

    elif menu == "✍️ 상담 기록 작성":
        st.title("✍️ 상담 기록 작성")
        try:
            # 학생 선택
            s_res = supabase.table("student_records").select("학번, 이름").execute()
            s_list = [f"{s['학번']} {s['이름']}" for s in s_res.data]
            
            col1, col2 = st.columns(2)
            with col1:
                selected_s = st.selectbox("학생 선택", s_list)
                c_date = st.date_input("상담 일자", value=date.today())
            with col2:
                fields = st.multiselect("상담 분야", ["진학", "진로", "학업", "생활"])
                types = st.multiselect("상담 유형", ["학생대면", "학부모대면", "온라인", "유선"])
            
            content = st.text_area("상담 상세 내용", height=300)
            
            if st.button("상담 기록 저장"):
                sid = selected_s.split(" ")[0]
                sname = selected_s.split(" ")[1]
                supabase.table("counseling_records").insert({
                    "student_id": sid,
                    "student_name": sname,
                    "counseling_date": str(c_date),
                    "counseling_field": ", ".join(fields),
                    "counseling_types": ", ".join(types),
                    "counseling_content": content
                }).execute()
                st.success("기록이 안전하게 저장되었습니다!")
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
                        st.write(f"**분야:** {row['counseling_field']} | **유형:** {row['counseling_types']}")
                        st.info(row['counseling_content'])
            else: st.info("기록이 없습니다.")
        except Exception as e: st.error(f"오류: {e}")
