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

# ─── 커스텀 CSS ──────────────────────────────────
st.markdown("""
<style>
    .school-title { color: #1e3a8a; font-size: 32px; font-weight: 800; text-align: center; margin-top: 20px; }
    .sub-title { color: #64748b; font-size: 18px; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #1e3a8a; color: white; font-weight: bold; }
    /* 삭제 버튼 전용 스타일 (빨간색) */
    .stButton>button.delete-btn { background-color: #ef4444; color: white; }
    .stButton>button.delete-btn:hover { background-color: #dc2626; }
</style>
""", unsafe_allow_html=True)

# ─── 로그인 상태 초기화 ───────────────────────────
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None

# ─── 로그인 함수 ──────────────────────────────────
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        role_res = supabase.table("user_roles").select("role").eq("user_id", res.user.id).execute()
        if role_res.data: st.session_state.role = role_res.data[0]["role"]
        return True
    except: return False

# ─── 메인 로직 ──────────────────────────────────
if st.session_state.user is None:
    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown('<div class="school-title">🏫 해운대중학교</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-title">진학상담 시스템 로그인을 환영합니다.</div>', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])
        with tab1:
            email = st.text_input("이메일 주소", key="login_email")
            pw = st.text_input("비밀번호", type="password", key="login_pw")
            if st.button("로그인"):
                if login(email, pw): st.rerun()
                else: st.error("정보를 확인해주세요.")
    st.stop()

else:
    with st.sidebar:
        st.markdown(f"### 👤 안녕하세요")
        is_admin = (st.session_state.role == "admin")
        if is_admin: st.info(f"{st.session_state.user.email} (관리자)")
        else: st.success(f"{st.session_state.user.email}")
        if st.button("로그아웃"):
            st.session_state.user = None
            st.rerun()
        st.divider()
        menu = st.radio("📋 메뉴 선택", ["🏠 학생 목록", "✍️ 상담 기록 작성", "🔍 상담 기록 조회"])

    # 1. 학생 목록
    if menu == "🏠 학생 목록":
        st.title("🏠 학생 목록 (3학년)")
        try:
            res = supabase.table("student_records").select("*").execute()
            if res.data:
                df = pd.DataFrame(res.data)
                cols = ["학번", "이름", "희망학교1", "희망학교2", "희망학교3", "희망직업(본인)", "희망직업(부모)"]
                df_display = df[[c for c in cols if c in df.columns]].copy()
                df_display.columns = ["학번", "이름", "1지망", "2지망", "3지망", "학생 희망직업", "학부모 희망직업"]
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else: st.info("학생 데이터가 없습니다.")
        except Exception as e: st.error(f"오류: {e}")

    # 2. 상담 기록 작성
    elif menu == "✍️ 상담 기록 작성":
        st.title("✍️ 상담 기록 작성")
        try:
            s_res = supabase.table("student_records").select("학번, 이름").execute()
            s_list = [f"{s['학번']} {s['이름']}" for s in s_res.data]
            
            col1, col2 = st.columns(2)
            with col1:
                selected_s = st.selectbox("학생 선택", s_list)
                c_date = st.date_input("상담 일자", value=date.today())
            with col2:
                fields = st.multiselect("상담 분야", ["진학", "진로", "학업", "생활", "기타"])
                types = st.multiselect("상담 유형", ["학생대면", "학부모대면", "학생온라인", "학부모온라인", "학부모유선"])
            
            content = st.text_area("상담 상세 내용", height=300)
            
            if st.button("상담 기록 저장"):
                sid, sname = selected_s.split(" ")
                supabase.table("counseling_records").insert({
                    "student_id": sid, "student_name": sname,
                    "counseling_date": str(c_date),
                    "counseling_field": ", ".join(fields),
                    "counseling_types": ", ".join(types),
                    "counseling_content": content
                }).execute()
                st.success(f"{sname} 학생의 기록이 저장되었습니다.")
        except Exception as e: st.error(f"오류: {e}")

    # 3. 상담 기록 조회 (삭제 버튼 추가!)
    elif menu == "🔍 상담 기록 조회":
        st.title("🔍 상담 기록 조회")
        try:
            res = supabase.table("counseling_records").select("*").order("counseling_date", desc=True).execute()
            if res.data:
                df = pd.DataFrame(res.data)
                search = st.text_input("🔍 학생 이름으로 검색")
                if search: df = df[df["student_name"].str.contains(search)]
                
                for _, row in df.iterrows():
                    title = f"📅 {row['counseling_date']} | {row['student_name']} ({row['student_id']})"
                    with st.expander(title):
                        st.write(f"**분야:** {row.get('counseling_field', '미지정')} | **유형:** {row.get('counseling_types', '미지정')}")
                        st.markdown("---")
                        st.write(row['counseling_content'])
                        
                        # 💡 관리자 전용 삭제 버튼
                        if is_admin:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button(f"🗑️ 기록 삭제 ({row['id']})", key=f"del_{row['id']}"):
                                try:
                                    supabase.table("counseling_records").delete().eq("id", row['id']).execute()
                                    st.success("기록이 성공적으로 삭제되었습니다.")
                                    st.rerun() # 삭제 후 목록 갱신
                                except Exception as e:
                                    st.error(f"삭제 실패: {e}")
            else: st.info("기록이 없습니다.")
        except Exception as e: st.error(f"오류: {e}")
