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
        padding-top: 0.8rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
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
        padding: 8px 14px;
        border-radius: 8px;
        font-size: 1.05rem;
        font-weight: 700;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .app-header .badge {
        font-size: 0.7rem;
        background-color: #334155;
        color: #cbd5e1;
        padding: 2px 6px;
        border-radius: 10px;
    }

    .stat-card {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 8px 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        margin-bottom: 4px;
    }
    .card-in { background-color: #f0fdf4; border-color: #bbf7d0; }
    .card-out { background-color: #fef2f2; border-color: #fecaca; }
    .card-bal { background-color: #f0f9ff; border-color: #bae6fd; }
    
    .stat-title { font-size: 0.75rem; color: #475569; font-weight: 600; }
    .stat-value { font-size: 1.15rem; font-weight: 700; }
    .val-in { color: #166534; }
    .val-out { color: #991b1b; }
    .val-bal { color: #075985; }

    .panel-header {
        font-size: 0.85rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 6px;
    }

    .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        height: 38px !important;
        width: 100% !important;
        white-space: nowrap !important;
        padding: 0 8px !important;
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
    df_res = pd.DataFrame(response.data)

    if not df_res.empty:
      # note 컬럼을 최우선적으로 매핑하고 그 외 알려진 적요 컬럼 확인
      for col in ["note", "description", "memo", "details", "content", "title"]:
        if col in df_res.columns:
          df_res["description"] = df_res[col]
          break

      if "description" not in df_res.columns:
        df_res["description"] = ""

      df_res["description"] = (
          df_res["description"].fillna("").astype(str).str.strip()
      )

    return df_res
  except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    return pd.DataFrame(columns=["id", "date", "type", "description", "amount"])


if "selected_row" not in st.session_state:
  st.session_state.selected_row = None

# ==========================================
# 3. 최상단 타이틀 바 및 현황판
# ==========================================
st.markdown(
    """
<div class="app-header">
    <span>🏦 입출금 관리</span>
    <span class="badge">Cloud</span>
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
      f"""<div class="stat-card card-in"><div class="stat-title">📥 총 입금</div><div class="stat-value val-in">₩ {total_in:,.0f}</div></div>""",
      unsafe_allow_html=True,
  )
with c2:
  st.markdown(
      f"""<div class="stat-card card-out"><div class="stat-title">📤 총 출금</div><div class="stat-value val-out">₩ {total_out:,.0f}</div></div>""",
      unsafe_allow_html=True,
  )
with c3:
  st.markdown(
      f"""<div class="stat-card card-bal"><div class="stat-title">💰 현재 잔액</div><div class="stat-value val-bal">₩ {balance:,.0f}</div></div>""",
      unsafe_allow_html=True,
  )

st.write("")

# ==========================================
# 4. 모바일/PC 겸용 컨트롤 영역
# ==========================================
tab_input, tab_select, tab_data = st.tabs(
    ["📥 신규 입력", "✏️ 선택 항목 수정/삭제", "⚙️ 데이터 관리"]
)

# --- [탭 1: 신규 거래 입력] ---
with tab_input:
  with st.container(border=True):
    in_col1, in_col2 = st.columns([1, 1])
    with in_col1:
      tx_date = st.date_input("날짜", datetime.now())
      tx_amount = st.number_input("금액 (원)", min_value=0, step=1000, value=0)
    with in_col2:
      tx_desc = st.text_input("적요", placeholder="내용 입력")
      st.write("")
      btn_c1, btn_c2 = st.columns(2)
      with btn_c1:
        if st.button("📥 입금 저장", type="primary"):
          if tx_desc and tx_amount > 0:
            supabase.table("transactions").insert({
                "date": str(tx_date),
                "type": "입금",
                "description": tx_desc,
                "note": tx_desc,
                "amount": tx_amount,
            }).execute()
            st.rerun()
          else:
            st.warning("적요와 금액을 입력하세요.")
      with btn_c2:
        if st.button("📤 출금 저장"):
          if tx_desc and tx_amount > 0:
            supabase.table("transactions").insert({
                "date": str(tx_date),
                "type": "출금",
                "description": tx_desc,
                "note": tx_desc,
                "amount": tx_amount,
            }).execute()
            st.rerun()
          else:
            st.warning("적요와 금액을 입력하세요.")

# --- [탭 2: 선택 항목 관리] ---
with tab_select:
  with st.container(border=True):
    sel = st.session_state.selected_row
    if sel is not None:
      try:
        default_date = datetime.strptime(
            str(sel["date"])[:10], "%Y-%m-%d"
        ).date()
      except Exception:
        default_date = datetime.now().date()

      default_desc = str(sel["description"])
      default_type = "입금" if "입금" in str(sel["type"]) else "출금"
      default_amount = int(sel["amount_val"])

      sc1, sc2 = st.columns(2)
      with sc1:
        edit_date = st.date_input("수정 날짜", value=default_date)
        edit_desc = st.text_input("수정 적요", value=default_desc)
      with sc2:
        edit_type = st.selectbox(
            "구분",
            options=["입금", "출금"],
            index=0 if default_type == "입금" else 1,
        )
        edit_amount = st.number_input(
            "수정 금액", min_value=0, step=1000, value=default_amount
        )

      s_btn1, s_btn2 = st.columns(2)
      with s_btn1:
        if st.button("💾 수정 완료", type="primary"):
          supabase.table("transactions").update({
              "date": str(edit_date),
              "type": edit_type,
              "description": edit_desc,
              "note": edit_desc,
              "amount": edit_amount,
          }).eq("id", int(sel["id"])).execute()
          st.session_state.selected_row = None
          st.success("수정 완료!")
          st.rerun()
      with s_btn2:
        if st.button("🗑️ 항목 삭제"):
          supabase.table("transactions").delete().eq(
              "id", int(sel["id"])
          ).execute()
          st.session_state.selected_row = None
          st.rerun()
    else:
      st.info("👇 아래 거래 내역 목록에서 수정할 항목을 클릭하세요.")

# --- [탭 3: 데이터 관리] ---
with tab_data:
  with st.container(border=True):
    if not df.empty:
      csv_data = df.to_csv(index=False).encode("utf-8-sig")
      json_data = df.to_json(orient="records", force_ascii=False)

      d_col1, d_col2 = st.columns(2)
      with d_col1:
        st.download_button(
            "📊 엑셀 다운로드",
            data=csv_data,
            file_name=f"입출금내역_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
      with d_col2:
        st.download_button(
            "💾 백업 파일 다운",
            data=json_data,
            file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
        )

      st.write("---")
      uploaded_file = st.file_uploader(
          "📂 복원 파일 선택 (.json)", type=["json"]
      )
      if uploaded_file is not None:
        try:
          restore_json = json.load(uploaded_file)

          # 백업 파일 구조 자동 분석 (history 배열 또는 일반 리스트 지원)
          if isinstance(restore_json, dict) and "history" in restore_json:
            records = restore_json["history"]
          elif isinstance(restore_json, list):
            records = restore_json
          else:
            records = []

          # DB 저장을 위해 규격 통일 (note -> description 및 note 동시 생성)
          formatted_records = []
          for r in records:
            desc = r.get("note") or r.get("description") or ""
            formatted_records.append({
                "date": str(r.get("date"))[:10],
                "type": r.get("type", "출금"),
                "description": desc,
                "note": desc,
                "amount": int(r.get("amount", 0)),
            })

          if formatted_records:
            supabase.table("transactions").delete().neq("id", 0).execute()
            supabase.table("transactions").insert(formatted_records).execute()
            st.success("복원 완료!")
            st.rerun()
          else:
            st.error("복원할 데이터 형식이 올바르지 않습니다.")
        except Exception as e:
          st.error(f"복원 실패: {e}")

st.write("")

# ==========================================
# 5. 하단 거래 내역 목록
# ==========================================
with st.container(border=True):
  st.markdown(
      '<div class="panel-header">📋 거래 내역 목록 <span'
      ' style="font-size:0.7rem; font-weight:normal; color:#64748b;">(항목 터치'
      " 시 수정 탭으로 연결)</span></div>",
      unsafe_allow_html=True,
  )

  if not df.empty:
    df_calc = df.sort_values(by=["date", "id"], ascending=[True, True]).copy()
    df_calc["amount_val"] = df_calc["amount"]

    df_calc["signed_amount"] = df_calc.apply(
        lambda r: r["amount"] if r["type"] == "입금" else -r["amount"], axis=1
    )
    df_calc["balance"] = df_calc["signed_amount"].cumsum()

    df_display = (
        df_calc.sort_values(by=["date", "id"], ascending=[False, False])
        .reset_index(drop=True)
        .copy()
    )

    df_display["type_display"] = df_display["type"]
    df_display["amount_display"] = df_display.apply(
        lambda r: f"+ {r['amount']:,} 원"
        if r["type"] == "입금"
        else f"- {r['amount']:,} 원",
        axis=1,
    )

    view_df = df_display[[
        "id",
        "date",
        "type_display",
        "description",
        "amount_display",
        "balance",
    ]].copy()

    def highlight_type(val):
      if val == "입금":
        return "background-color: #e0f2fe; color: #0369a1; font-weight: bold;"
      elif val == "출금":
        return "background-color: #ffe4e6; color: #be123c; font-weight: bold;"
      return ""

    styled_df = view_df.style.map(highlight_type, subset=["type_display"])

    event = st.dataframe(
        styled_df,
        use_container_width=True,
        height=380,
        column_config={
            "id": st.column_config.NumberColumn("ID"),
            "date": st.column_config.DateColumn("날짜", format="YYYY-MM-DD"),
            "type_display": st.column_config.TextColumn("구분"),
            "description": st.column_config.TextColumn("적요"),
            "amount_display": st.column_config.TextColumn("금액"),
            "balance": st.column_config.NumberColumn(
                "잔액 (원)", format="%d 원"
            ),
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-cell",
    )

    selection = event.selection
    clicked_idx = None

    if selection and "cells" in selection and len(selection["cells"]) > 0:
      cell = selection["cells"][0]
      if isinstance(cell, (list, tuple)):
        clicked_idx = cell[0]
      elif isinstance(cell, dict):
        clicked_idx = cell.get("row")

    if clicked_idx is not None and clicked_idx < len(df_display):
      selected_data = df_display.iloc[clicked_idx].to_dict()

      if (
          st.session_state.selected_row is None
          or st.session_state.selected_row.get("id") != selected_data["id"]
      ):
        st.session_state.selected_row = selected_data
        st.rerun()
  else:
    st.info("표시할 거래 내역이 없습니다.")
