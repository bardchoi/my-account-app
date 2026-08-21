import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import json
import os

# ==========================================
# 1. 페이지 기본 설정 (와이드 레이아웃 & CSS 적용)
# ==========================================
st.set_page_config(
    page_title="입출금 관리 프로그램",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 눈이 편안한 아이케어 파스텔 테마 & 전체 고정 스크롤 CSS
st.markdown("""
<style>
    /* 기본 여백 및 배경 설정 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    
    body, [data-testid="stAppViewContainer"] {
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Top Title Bar */
    .app-header {
        background-color: #0f172a;
        color: #f8fafc;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: 700;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .app-header .badge {
        font-size: 0.75rem;
        background-color: #334155;
        color: #cbd5e1;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 400;
    }

    /* Summary Cards */
    .stat-card {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 10px 14px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .card-in { background-color: #f0fdf4; }
    .card-out { background-color: #fef2f2; }
    .card-bal { background-color: #f0f9ff; }
    
    .stat-title { font-size: 0.75rem; color: #64748b; font-weight: 600; margin-bottom: 2px; }
    .stat-value { font-size: 1.25rem; font-weight: 700; }
    .val-in { color: #15803d; }
    .val-out { color: #b91c1c; }
    .val-bal { color: #0369a1; }

    /* Control Panel Box */
    .panel-box {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .panel-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
    }

    /* Streamlit 요소 커스텀 */
    div[data-baseweb="input"] {
        background-color: #f8fafc !important;
        border-color: #cbd5e1 !important;
    }
    
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        height: 38px !important;
        width: 100% !important;
    }
    
    /* 데이터프레임 고정 스크롤 */
    .stDataFrame {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Supabase 연동 설정 (Render 환경변수 및 secrets 호환)
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY", "")
    return create_client(url, key)

supabase = init_supabase()

def fetch_data():
    try:
        response = supabase.table("transactions").select("*").order("date", desc=True).order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(columns=["id", "date", "type", "description", "amount"])

# ==========================================
# 3. 최상단 타이틀 바 및 현황판
# ==========================================
st.markdown("""
<div class="app-header">
    <span>🏦 입출금 관리 프로그램</span>
    <span class="badge">Cloud Synced</span>
</div>
""", unsafe_allow_html=True)

df = fetch_data()

# 잔액 및 입출금 계산
total_in = df[df['type'] == '입금']['amount'].sum() if not df.empty else 0
total_out = df[df['type'] == '출금']['amount'].sum() if not df.empty else 0
balance = total_in - total_out

# 상단 현황 카드 3개
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""
    <div class="stat-card card-in">
        <div class="stat-title">📥 총 입금액</div>
        <div class="stat-value val-in">₩ {total_in:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="stat-card card-out">
        <div class="stat-title">📤 총 출금액</div>
        <div class="stat-value val-out">₩ {total_out:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="stat-card card-bal">
        <div class="stat-title">💰 현재 잔액</div>
        <div class="stat-value val-bal">₩ {balance:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("") # 간격 조정

# ==========================================
# 4. 중앙 제어 컨트롤 영역 (비대칭 비율: 1.8 : 1.4 : 0.8)
# ==========================================
col_input, col_select, col_data = st.columns([1.8, 1.4, 0.8])

# Session state 초기화
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

# --- [1열: 신규 거래 입력 (넓은 영역 & 적요 칸 확장)] ---
with col_input:
    st.markdown('<div class="panel-title">📥 신규 거래 입력</div>', unsafe_allow_html=True)
    
    in_col1, in_col2 = st.columns([1, 2.2])
    with in_col1:
        tx_date = st.date_input("날짜", datetime.now(), label_visibility="collapsed")
    with in_col2:
        tx_desc = st.text_input("적요", placeholder="적요 입력", label_visibility="collapsed")
        
    in_col3, in_btn1, in_btn2 = st.columns([1.8, 1, 1])
    with in_col3:
        tx_amount = st.number_input("금액", min_value=0, step=1000, value=0, label_visibility="collapsed")
    with in_btn1:
        if st.button("📥 입금", type="primary"):
            if tx_desc and tx_amount > 0:
                supabase.table("transactions").insert({
                    "date": str(tx_date),
                    "type": "입금",
                    "description": tx_desc,
                    "amount": tx_amount
                }).execute()
                st.rerun()
            else:
                st.warning("적요와 금액을 확인해주세요.")
    with in_btn2:
        if st.button("📤 출금"):
            if tx_desc and tx_amount > 0:
                supabase.table("transactions").insert({
                    "date": str(tx_date),
                    "type": "출금",
                    "description": tx_desc,
                    "amount": tx_amount
                }).execute()
                st.rerun()
            else:
                st.warning("적요와 금액을 확인해주세요.")

# --- [2열: 선택 항목 관리 (확장 영역)] ---
with col_select:
    st.markdown('<div class="panel-title">📊 선택 항목 관리</div>', unsafe_allow_html=True)
    
    if not df.empty:
        options = {row['id']: f"[{row['date']}] {row['type']} | {row['description']} ({row['amount']:,}원)" for _, row in df.iterrows()}
        selected_option = st.selectbox("항목 선택", options=list(options.keys()), format_func=lambda x: options[x], label_visibility="collapsed")
        
        sel_btn1, sel_btn2 = st.columns(2)
        with sel_btn1:
            if st.button("✏️ 거래 수정"):
                st.session_state.edit_id = selected_option
                st.info("아래 테이블에서 바로 수정이 가능합니다.")
        with sel_btn2:
            if st.button("🗑️ 거래 삭제"):
                supabase.table("transactions").delete().eq("id", selected_option).execute()
                st.rerun()
    else:
        st.info("등록된 거래 내역이 없습니다.")

# --- [3열: 데이터 관리 (컴팩트 영역)] ---
with col_data:
    st.markdown('<div class="panel-title">⚙️ 데이터 관리</div>', unsafe_allow_html=True)
    
    if not df.empty:
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📊 엑셀 저장", data=csv_data, file_name=f"입출금내역_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
        
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            json_data = df.to_json(orient="records", force_ascii=False)
            st.download_button("💾 백업", data=json_data, file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json")
        with d_col2:
            uploaded_file = st.file_uploader("📂 복원", type=["json"], label_visibility="collapsed")
            if uploaded_file is not None:
                try:
                    restore_data = json.load(uploaded_file)
                    supabase.table("transactions").delete().neq("id", 0).execute()
                    supabase.table("transactions").insert(restore_data).execute()
                    st.success("복원 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"복원 실패: {e}")

st.write("") # 간격 조정

# ==========================================
# 5. 하단 거래 내역 테이블 (내부 스크롤 고정)
# ==========================================
st.markdown('<div class="panel-title">📋 거래 내역 목록</div>', unsafe_allow_html=True)

if not df.empty:
    df_calc = df.sort_values(by=["date", "id"], ascending=[True, True]).copy()
    df_calc['signed_amount'] = df_calc.apply(lambda r: r['amount'] if r['type'] == '입금' else -r['amount'], axis=1)
    df_calc['balance'] = df_calc['signed_amount'].cumsum()
    
    df_display = df_calc.sort_values(by=["date", "id"], ascending=[False, False]).copy()
    
    display_df = df_display[['date', 'type', 'description', 'amount', 'balance']].copy()
    display_df.columns = ['날짜', '구분', '적요', '금액 (원)', '잔액 (원)']
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=380,
        column_config={
            "금액 (원)": st.column_config.NumberColumn(format="%d 원"),
            "잔액 (원)": st.column_config.NumberColumn(format="%d 원"),
            "날짜": st.column_config.DateColumn(format="YYYY-MM-DD")
        },
        hide_index=True
    )
else:
    st.info("표시할 거래 내역이 없습니다.")
