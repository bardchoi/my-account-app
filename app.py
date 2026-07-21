import csv
import datetime
import io
import json
import os
import urllib.request
from flask import Flask, jsonify, render_template_string, request, send_file

app = Flask(__name__)

# =========================================================
# 🔑 Supabase 정보 입력
# =========================================================
SUPABASE_URL = "https://whunucledtdqtxjqyoyg.supabase.co/rest/v1/"  # 본인 URL
SUPABASE_KEY = "sb_publishable_gwv-otmc5S9ytdHRViA1uA_8HUaY68d"  # 본인 Publishable Key
# =========================================================


def supabase_request(method, endpoint, payload=None):
  url = f"{SUPABASE_URL}/rest/v1/{endpoint}"
  headers = {
      "apikey": SUPABASE_KEY,
      "Authorization": f"Bearer {SUPABASE_KEY}",
      "Content-Type": "application/json",
      "Prefer": "return=representation",
  }
  data = json.dumps(payload).encode("utf-8") if payload else None
  req = urllib.request.Request(url, data=data, headers=headers, method=method)
  try:
    with urllib.request.urlopen(req) as response:
      res_body = response.read().decode("utf-8")
      return json.loads(res_body) if res_body else []
  except Exception as e:
    print(f"DB Error: {e}")
    return None


def load_data():
  res = supabase_request("GET", "account_data?id=eq.1")
  if res and len(res) > 0:
    return res[0]["content"]

  default_data = {"owner": "홍길동", "balance": 0, "history": []}
  supabase_request(
      "POST", "account_data", {"id": 1, "content": default_data}
  )
  return default_data


def save_data(data):
  supabase_request("PATCH", "account_data?id=eq.1", {"content": data})


def recalculate_balances(history):
  running_balance = 0
  today = datetime.datetime.now().strftime("%Y-%m-%d")
  for item in history:
    # 예전 백업 데이터에 date 항목이 없거나 None인 경우 기본값 처리
    if not item.get("date"):
      item["date"] = today

    if item.get("type") == "입금":
      running_balance += item.get("amount", 0)
    else:
      running_balance -= item.get("amount", 0)
    item["balance"] = running_balance
  return running_balance


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 스마트 입출금 및 장부 관리</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: '맑은 고딕', sans-serif; margin: 0; padding: 12px; background-color: #f4f6f9; }
        
        .card { background: white; padding: 16px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 12px; }
        .card h2, .card h3 { margin: 0 0 10px 0; color: #1F4E79; }
        .balance { font-size: 1.6rem; font-weight: bold; color: #1F4E79; text-align: right; }
        
        input, select { width: 100%; padding: 10px; margin: 6px 0; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; }
        label { font-weight: bold; font-size: 0.9rem; color: #333; margin-top: 6px; display: block; }
        
        .btn-group { display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
        button { flex: 1; min-width: 80px; padding: 10px; border: none; border-radius: 6px; font-size: 0.95rem; font-weight: bold; color: white; cursor: pointer; }
        
        .btn-deposit { background-color: #2E7D32; }
        .btn-withdraw { background-color: #C62828; }
        .btn-excel { background-color: #1D6F42; }
        .btn-backup { background-color: #0277BD; }
        .btn-restore { background-color: #E65100; }
        .btn-main-edit { background-color: #1976D2; }
        .btn-main-delete { background-color: #D32F2F; }
        .btn-cancel { background-color: #757575; }

        table { width: 100%; border-collapse: collapse; margin-top: 8px; background: white; }
        th, td { border: 1px solid #e0e0e0; padding: 8px 4px; text-align: center; font-size: 0.9rem; }
        th { background-color: #1F4E79; color: white; }
        
        .col-date { width: 22%; }
        .col-type { width: 12%; white-space: nowrap; }
        .col-note { width: 34%; }
        .col-amount { width: 16%; }
        .col-balance { width: 16%; }

        tbody tr { cursor: pointer; transition: background-color 0.2s; }
        tbody tr:hover { background-color: #f1f5f9; }
        tbody tr.selected-row { background-color: #FFF9C4 !important; border: 2px solid #FBC02D; font-weight: bold; }
        
        .type-deposit { color: #2E7D32; font-weight: bold; background-color: #E8F5E9; }
        .type-withdraw { color: #C62828; font-weight: bold; background-color: #FFEBEE; }
        
        .text-left { text-align: left; }
        .text-right { text-align: right; }

        .modal { display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
        .modal-content { background: white; margin: 10% auto; padding: 20px; width: 90%; max-width: 400px; border-radius: 12px; }
        .selected-info { font-size: 0.85rem; color: #555; margin-bottom: 8px; }
    </style>
</head>
<body>

    <div class="card">
        <h2>🏦 클라우드 입출금 관리</h2>
        <div class="balance" id="balanceView">현재 잔액: 0 원</div>
    </div>

    <div class="card">
        <h3>📥📤 거래 입력</h3>
        <label for="dateInput">날짜 (연월일)</label>
        <input type="date" id="dateInput">
        
        <input type="text" id="noteInput" placeholder="적요 (내용)">
        <input type="number" id="amountInput" placeholder="금액 (원)">
        <div class="btn-group">
            <button class="btn-deposit" onclick="addTransaction('입금')">📥 입금하기</button>
            <button class="btn-withdraw" onclick="addTransaction('출금')">📤 출금하기</button>
        </div>
    </div>

    <div class="card">
        <h3>📊 거래 내역 관리</h3>
        <div class="selected-info" id="selectedStatus">👉 관리할 항목을 목록에서 클릭해 선택하세요.</div>
        <div class="btn-group">
            <button class="btn-main-edit" onclick="triggerEdit()">✏️ 선택 항목 수정</button>
            <button class="btn-main-delete" onclick="triggerDelete()">🗑️ 선택 항목 삭제</button>
        </div>
    </div>

    <div class="card">
        <h3>⚙️ 데이터 백업 & 내보내기</h3>
        <div class="btn-group">
            <button class="btn-excel" onclick="downloadExcel()">📊 엑셀(CSV) 저장</button>
            <button class="btn-backup" onclick="backupData()">💾 데이터 백업</button>
            <button class="btn-restore" onclick="document.getElementById('fileInput').click()">📂 데이터 복원</button>
            <input type="file" id="fileInput" style="display:none;" accept=".json" onchange="restoreData(event)">
        </div>
    </div>

    <div class="card">
        <h3>📋 거래 내역 (클릭하여 선택)</h3>
        <table>
            <thead>
                <tr>
                    <th class="col-date">날짜</th>
                    <th class="col-type">구분</th>
                    <th class="col-note">적요</th>
                    <th class="col-amount">금액</th>
                    <th class="col-balance">잔액</th>
                </tr>
            </thead>
            <tbody id="historyTable"></tbody>
        </table>
    </div>

    <div id="editModal" class="modal">
        <div class="modal-content">
            <h3>✏️ 선택 항목 수정</h3>
            <input type="hidden" id="editIndex">
            
            <label>날짜</label>
            <input type="date" id="editDate">
            
            <label>구분</label>
            <select id="editType">
                <option value="입금">입금</option>
                <option value="출금">출금</option>
            </select>
            
            <label>적요</label>
            <input type="text" id="editNote">
            
            <label>금액</label>
            <input type="number" id="editAmount">
            
            <div class="btn-group" style="margin-top: 12px;">
                <button class="btn-deposit" onclick="saveEdit()">수정 완료</button>
                <button class="btn-cancel" onclick="closeEditModal()">취소</button>
            </div>
        </div>
    </div>

    <script>
        let currentHistory = [];
        let selectedIndex = -1;

        function setDefaultDate() {
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('dateInput').value = today;
        }

        async function fetchHistory() {
            const res = await fetch('/api/data');
            const data = await res.json();
            currentHistory = data.history || [];
            selectedIndex = -1;
            updateSelectedStatus();
            
            document.getElementById('balanceView').innerText = `현재 잔액: ${ (data.balance || 0).toLocaleString() } 원`;
            
            const tbody = document.getElementById('historyTable');
            tbody.innerHTML = '';
            
            for (let i = currentHistory.length - 1; i >= 0; i--) {
                const item = currentHistory[i];
                const typeClass = item.type === '입금' ? 'type-deposit' : 'type-withdraw';
                const displayDate = item.date ? item.date.split(' ')[0] : '-';
                const itemAmount = item.amount || 0;
                const itemBalance = item.balance || 0;
                
                const row = `<tr id="row-${i}" onclick="selectRow(${i})">
                    <td>${displayDate}</td>
                    <td class="${typeClass}">${item.type || '-'}</td>
                    <td class="text-left">${item.note || '-'}</td>
                    <td class="text-right">${itemAmount.toLocaleString()}</td>
                    <td class="text-right">${itemBalance.toLocaleString()}</td>
                </tr>`;
                tbody.innerHTML += row;
            }
        }

        function selectRow(index) {
            if (selectedIndex !== -1) {
                const prevRow = document.getElementById(`row-${selectedIndex}`);
                if (prevRow) prevRow.classList.remove('selected-row');
            }
            
            if (selectedIndex === index) {
                selectedIndex = -1;
            } else {
                selectedIndex = index;
                const currentRow = document.getElementById(`row-${index}`);
                if (currentRow) currentRow.classList.add('selected-row');
            }
            updateSelectedStatus();
        }

        function updateSelectedStatus() {
            const statusDiv = document.getElementById('selectedStatus');
            if (selectedIndex === -1) {
                statusDiv.innerText = '👉 관리할 항목을 목록에서 클릭해 선택하세요.';
                statusDiv.style.color = '#555';
            } else {
                const item = currentHistory[selectedIndex];
                const dateStr = item.date ? item.date.split(' ')[0] : '-';
                const amountStr = (item.amount || 0).toLocaleString();
                statusDiv.innerText = `✅ 선택됨: [${dateStr}] [${item.type}] ${item.note} (${amountStr}원)`;
                statusDiv.style.color = '#1976D2';
            }
        }

        async function addTransaction(type) {
            const dateInput = document.getElementById('dateInput');
            const noteInput = document.getElementById('noteInput');
            const amountInput = document.getElementById('amountInput');
            
            const date = dateInput.value || new Date().toISOString().split('T')[0];
            const note = noteInput.value.trim() || '내용 없음';
            const amount = parseInt(amountInput.value);

            if (!amount || amount <= 0) {
                alert('올바른 금액을 입력해 주세요.');
                return;
            }

            await fetch('/api/transaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date, type, note, amount })
            });

            noteInput.value = '';
            amountInput.value = '';
            setDefaultDate();
            fetchHistory();
        }

        function triggerEdit() {
            if (selectedIndex === -1) {
                alert('수정할 항목을 목록에서 먼저 선택해 주세요.');
                return;
            }
            const item = currentHistory[selectedIndex];
            document.getElementById('editIndex').value = selectedIndex;
            document.getElementById('editDate').value = item.date ? item.date.split(' ')[0] : new Date().toISOString().split('T')[0];
            document.getElementById('editType').value = item.type || '입금';
            document.getElementById('editNote').value = item.note || '';
            document.getElementById('editAmount').value = item.amount || 0;
            document.getElementById('editModal').style.display = 'block';
        }

        function closeEditModal() {
            document.getElementById('editModal').style.display = 'none';
        }

        async function saveEdit() {
            const index = parseInt(document.getElementById('editIndex').value);
            const date = document.getElementById('editDate').value;
            const type = document.getElementById('editType').value;
            const note = document.getElementById('editNote').value.trim() || '내용 없음';
            const amount = parseInt(document.getElementById('editAmount').value);

            if (!amount || amount <= 0) {
                alert('올바른 금액을 입력해 주세요.');
                return;
            }

            await fetch('/api/transaction/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index, date, type, note, amount })
            });

            closeEditModal();
            fetchHistory();
        }

        async function triggerDelete() {
            if (selectedIndex === -1) {
                alert('삭제할 항목을 목록에서 먼저 선택해 주세요.');
                return;
            }
            const item = currentHistory[selectedIndex];
            if (!confirm(`선택한 항목 [${item.note} - ${(item.amount||0).toLocaleString()}원]을 삭제하시겠습니까?`)) return;

            await fetch('/api/transaction/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index: selectedIndex })
            });

            fetchHistory();
        }

        function downloadExcel() { window.location.href = '/api/download_excel'; }
        function backupData() { window.location.href = '/api/backup'; }

        async function restoreData(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/api/restore', { method: 'POST', body: formData });
            const result = await res.json();
            if (result.status === 'success') {
                alert('데이터가 성공적으로 복원되었습니다.');
                fetchHistory();
            } else {
                alert('복원 실패: 파일 형식이나 내용을 확인해주세요.');
            }
            event.target.value = '';
        }

        setDefaultDate();
        fetchHistory();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
  return render_template_string(HTML_TEMPLATE)


@app.route("/api/data", methods=["GET"])
def get_data():
  return jsonify(load_data())


@app.route("/api/transaction", methods=["POST"])
def add_transaction():
  req = request.json
  data = load_data()

  if "history" not in data:
    data["history"] = []

  data["history"].append({
      "date": req.get("date"),
      "type": req["type"],
      "note": req["note"],
      "amount": req["amount"],
      "balance": 0,
  })

  data["balance"] = recalculate_balances(data["history"])
  save_data(data)
  return jsonify({"status": "success"})


@app.route("/api/transaction/edit", methods=["POST"])
def edit_transaction():
  req = request.json
  data = load_data()
  idx = req["index"]

  if "history" in data and 0 <= idx < len(data["history"]):
    data["history"][idx]["date"] = req.get("date")
    data["history"][idx]["type"] = req["type"]
    data["history"][idx]["note"] = req["note"]
    data["history"][idx]["amount"] = req["amount"]
    data["balance"] = recalculate_balances(data["history"])
    save_data(data)
    return jsonify({"status": "success"})
  return jsonify({"status": "error"}), 400


@app.route("/api/transaction/delete", methods=["POST"])
def delete_transaction():
  req = request.json
  data = load_data()
  idx = req["index"]

  if "history" in data and 0 <= idx < len(data["history"]):
    data["history"].pop(idx)
    data["balance"] = recalculate_balances(data["history"])
    save_data(data)
    return jsonify({"status": "success"})
  return jsonify({"status": "error"}), 400


@app.route("/api/download_excel", methods=["GET"])
def download_excel():
  data = load_data()
  output = io.StringIO()
  output.write("\ufeff")
  writer = csv.writer(output)

  writer.writerow(["일시", "구분", "적요", "금액", "잔액"])
  for item in data.get("history", []):
    writer.writerow([
        item.get("date", ""),
        item.get("type", ""),
        item.get("note", ""),
        item.get("amount", 0),
        item.get("balance", 0),
    ])

  mem = io.BytesIO()
  mem.write(output.getvalue().encode("utf-8"))
  mem.seek(0)
  filename = (
      f"account_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
  )
  return send_file(
      mem,
      as_attachment=True,
      download_name=filename,
      mimetype="text/csv; charset=utf-8",
  )


@app.route("/api/backup", methods=["GET"])
def backup_data():
  data = load_data()
  output = io.BytesIO(
      json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")
  )
  filename = f"account_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
  return send_file(
      output, as_attachment=True, download_name=filename, mimetype="application/json"
  )


@app.route("/api/restore", methods=["POST"])
def restore_data():
  if "file" not in request.files:
    return jsonify({"status": "error"}), 400
  file = request.files["file"]
  try:
    content = json.load(file)
    # 리스트 형태로 백업된 파일이거나 dict 구조인 경우 모두 대응
    if isinstance(content, list):
      history = content
      content = {"owner": "홍길동", "history": history}
    elif isinstance(content, dict) and "history" in content:
      history = content["history"]
    else:
      return jsonify({"status": "error", "message": "Invalid format"}), 400

    content["balance"] = recalculate_balances(history)
    save_data(content)
    return jsonify({"status": "success"})
  except Exception as e:
    print("Restore Error:", e)
    return jsonify({"status": "error"}), 400


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
