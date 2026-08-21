import json
from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import Client, create_client

# ==========================================
# 1. 페이지 기본 설정 및 CSS
# ==========================================
st.set_page_config(
    page_title="입출금 관리 프로그램",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    
    body, [data-testid="stAppViewContainer"] {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    header {visibility: hidden;}
    footer {visibility: hidden;}

    .app-header {
        background-color: #0f172a;
        color: #f8fafc;
        padding: 10px 18px;
        border-radius: 8px;
        font-size: 1.15rem;
        font-weight: 700;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .app-header .badge {
        font-size: 0.75rem;
        background-color: #334155;
        color: #cbd5e1;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 400;
    }

    .stat-card {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card-in { background-color: #f0fdf4; border-color: #bbf7d0; }
    .card-out { background-color: #fef2f2; border-color: #fecaca; }
    .card-bal { background-color: #f0f9ff; border-color: #bae6fd; }
    
    .stat-title { font-size: 0.8rem; color: #475569; font-weight: 600; margin-bottom: 4px; }
    .stat-value { font-size: 1.35rem; font-weight: 700; }
    .val-in { color: #166534; }
    .val-out { color: #991b1b; }
    .val-bal { color: #075985; }

    .panel-header {
        font-size: 0.9rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 8px;
    }

    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
    }
    
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        height: 38px !important;
        width: 100% !important;
    }
    
    .stDataFrame {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. Supabase DB 연동
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
  url = "https://whunucledtdqtxjqyoyg.supabase.co"
  key = "sb_publishable_gwv-otmc5S9ytdHRViA1uA_8HUaY68d"
  return create_client(url, key)


supabase = init_supabase()


def fetch_data():
  try:
    response = (
        supabase.table("transactions")
        .select("*")
        .order("date", desc=True)
        .order("id", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data)
  except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    return pd.DataFrame(columns=["id", "date", "type", "description", "amount"])


# Session State 초기화
if "selected_row" not in st.session_state:
  st.session_state.selected_row = None

# ==========================================
# 3. 최상단 타이틀 바 및 현황판
# ==========================================
st.markdown(
    """
<div class="app-header">
    <span>🏦 입출금 관리 프로그램</span>
    <span class="badge">Cloud Synced</span>
</div>
""",
    unsafe_allow_html=True,
)

df = fetch_data()

total_in = df[df["type"] == "입금"]["amount"].sum() if not df.empty else 0
total_out = df[df["type"] == "출금"]["amount"].sum() if not df.empty else 0
balance = total_in - total_out

c1, c2, c3 = st.columns(3)
with c1:
  st.markdown(
      f"""
    <div class="stat-card card-in">
        <div class="stat-title">📥 총 입금액</div>
        <div class="stat-value val-in">₩ {total_in:,.0f}</div>
    </div>
    """,
      unsafe_allow_html=True,
  )
with c2:
  st.markdown(
      f"""
    <div class="stat-card card-out">
        <div class="stat-title">📤 총 출금액</div>
        <div class="stat-value val-out">₩ {total_out:,.0f}</div>
    </div>
    """,
      unsafe_allow_html=True,
  )
with c3:
  st.markdown(
      f"""
    <div class="stat-card card-bal">
        <div class="stat-title">💰 현재 잔액</div>
        <div class="stat-value val-bal">₩ {balance:,.0f}</div>
    </div>
    """,
      unsafe_allow_html=True,
  )

st.write("")

# ==========================================
# 4. 중앙 제어 컨트롤 영역
# ==========================================
col_input, col_select, col_data = st.columns([1.5, 1.8, 1.0])

# --- [1열: 신규 거래 입력] ---
with col_input:
  with st.container(border=True):
    st.markdown(
        '<div class="panel-header">📥 신규 거래 입력</div>',
        unsafe_allow_html=True,
    )

    in_col1, in_col2 = st.columns([1, 1.8])
    with in_col1:
      tx_date = st.date_input(
          "신규 날짜", datetime.now(), label_visibility="collapsed"
      )
    with in_col2:
      tx_desc = st.text_input(
          "신규 적요", placeholder="적요 입력", label_visibility="collapsed"
      )

    in_col3, in_btn1, in_btn2 = st.columns([1.6, 1, 1])
    with in_col3:
      tx_amount = st.number_input(
          "신규 금액",
          min_value=0,
          step=1000,
          value=0,
          label_visibility="collapsed",
      )
    with in_btn1:
      if st.button("📥 입금", type="primary"):
        if tx_desc and tx_amount > 0:
          supabase.table("transactions").insert({
              "date": str(tx_date),
              "type": "입금",
              "description": tx_desc,
              "amount": tx_amount,
          }).execute()
          st.rerun()
        else:
          st.warning("적요와 금액을 입력하세요.")
    with in_btn2:
      if st.button("📤 출금"):
        if tx_desc and tx_amount > 0:
          supabase.table("transactions").insert({
              "date": str(tx_date),
              "type": "출금",
              "description": tx_desc,
              "amount": tx_amount,
          }).execute()
          st.rerun()
        else:
          st.warning("적요와 금액을 입력하세요.")

# --- [2열: 선택 항목 관리 (목록 클릭 시 자동 폼 채움)] ---
with col_select:
  with st.container(border=True):
    st.markdown(
        '<div class="panel-header">✏️ 선택 항목 관리 (목록 클릭 시'
        " 채워짐)</div>",
        unsafe_allow_html=True,
    )

    sel = st.session_state.selected_row

    if sel is not None:
      default_date = datetime.strptime(str(sel["date"]), "%Y-%m-%d").date()
      default_desc = str(sel["description"])
      default_type = "입금" if sel["type"] == "입금" else "출금"
      default_amount = int(sel["amount"])

      sc1, sc2, sc3 = st.columns([1, 1, 1.5])
      with sc1:
        edit_date = st.date_input("수정 날짜", value=default_date)
      with sc2:
        edit_type = st.selectbox(
            "구분",
            options=["입금", "출금"],
            index=0 if default_type == "입금" else 1,
        )
      with sc3:
        edit_desc = st.text_input("수정 적요", value=default_desc)

      sc4, sc5, sc6 = st.columns([1.5, 1, 1])
      with sc4:
        edit_amount = st.number_input(
            "수정 금액", min_value=0, step=1000, value=default_amount
        )
      with sc5:
        if st.button("💾 수정 저장", type="primary"):
          supabase.table("transactions").update({
              "date": str(edit_date),
              "type": edit_type,
              "description": edit_desc,
              "amount": edit_amount,
          }).eq("id", int(sel["id"])).execute()
          st.session_state.selected_row = None
          st.success("수정 완료!")
          st.rerun()
      with sc6:
        if st.button("🗑️ 삭제"):
          supabase.table("transactions").delete().eq(
              "id", int(sel["id"])
          ).execute()
          st.session_state.selected_row = None
          st.rerun()
    else:
      st.info("👇 아래 거래 내역 목록에서 임의의 항목을 클릭하세요.")

# --- [3열: 데이터 관리] ---
with col_data:
  with st.container(border=True):
    st.markdown(
        '<div class="panel-header">⚙️ 데이터 관리</div>',
        unsafe_allow_html=True,
    )

    if not df.empty:
      csv_data = df.to_csv(index=False).encode("utf-8-sig")
      d_col1, d_col2 = st.columns(2)
      with d_col1:
        st.download_button(
            "📊 엑셀",
            data=csv_data,
            file_name=f"입출금내역_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
      with d_col2:
        json_data = df.to_json(orient="records", force_ascii=False)
        st.download_button(
            "💾 백업",
            data=json_data,
            file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
        )

      uploaded_file = st.file_uploader(
          "📂 복원", type=["json"], label_visibility="collapsed"
      )
      if uploaded_file is not None:
        try:
          restore_data = json.load(uploaded_file)
          supabase.table("transactions").delete().neq("id", 0).execute()
          supabase.table("transactions").insert(restore_data).execute()
          st.success("복원 완료!")
          st.rerun()
        except Exception as e:
          st.error(f"복원 실패: {e}")

st.write("")

# ==========================================
# 5. 하단 거래 내역 목록 (체크박스 완전히 제거)
# ==========================================
with st.container(border=True):
  st.markdown(
      '<div class="panel-header">📋 거래 내역 목록 <span'
      ' style="font-size:0.75rem; font-weight:normal; color:#64748b;">(원하는'
      " 거래의 아무 위치나 클릭하면 위 '선택 항목 관리'로 정보가"
      " 입력됩니다)</span></div>",
      unsafe_allow_html=True,
  )

  if not df.empty:
    df_calc = df.sort_values(by=["date", "id"], ascending=[True, True]).copy()
    df_calc["signed_amount"] = df_calc.apply(
        lambda r: r["amount"] if r["type"] == "입금" else -r["amount"], axis=1
    )
    df_calc["balance"] = df_calc["signed_amount"].cumsum()

    df_display = df_calc.sort_values(
        by=["date", "id"], ascending=[False, False]
    ).copy()

    # 체크박스 없는 순수한 셀 클릭 감지 기능 (on_select="rerun" + selection_mode="single-cell")
    event = st.dataframe(
        df_display[["id", "date", "type", "description", "amount", "balance"]],
        use_container_width=True,
        height=400,
        column_config={
            "id": st.column_config.NumberColumn("ID"),
            "amount": st.column_config.NumberColumn(
                "금액 (원)", format="%d 원"
            ),
            "balance": st.column_config.NumberColumn(
                "잔액 (원)", format="%d 원"
            ),
            "date": st.column_config.DateColumn("날짜", format="YYYY-MM-DD"),
            "type": st.column_config.TextColumn("구분"),
            "description": st.column_config.TextColumn("적요"),
        },
        hide_index=True,
        selection_mode="single-cell",  # 체크박스 없이 셀 클릭으로만 동작
        on_select="rerun",
    )

    # 클릭된 셀의 행 정보를 가져와 session_state에 등록
    selected_cells = event.selection.get("cells", [])
    if selected_cells:
      clicked_row_idx = selected_cells[0][0]
      selected_data = df_display.iloc[clicked_row_idx].to_dict()

      if (
          st.session_state.selected_row is None
          or st.session_state.selected_row.get("id") != selected_data["id"]
      ):
        st.session_state.selected_row = selected_data
        st.rerun()
  else:
    st.info("표시할 거래 내역이 없습니다.")
