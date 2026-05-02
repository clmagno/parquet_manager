#!/usr/bin/env python3
"""
Parquet CRUD Editor with Instant Local Save
───────────────────────────────────────────
Drag-and-drop parquet files, inline edit, add rows, delete rows,
search data, and overwrite the file locally without downloading.
"""

import sys, os, io, json, threading, webbrowser, datetime
from typing import Any

# ── dependency bootstrap ───────────────────────────────────────────────────
def _ensure(packages: list[str]) -> None:
    import importlib, subprocess
    missing = [p for p in packages if not importlib.util.find_spec(p.split("[")[0])]
    if missing:
        print(f"  Installing: {', '.join(missing)} …")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
            stdout=subprocess.DEVNULL,
        )

_ensure(["flask", "pyarrow"])

from flask import Flask, request, jsonify, send_file
import pyarrow.parquet as pq
import pyarrow as pa

# ── flask app ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.urandom(24)

_store: dict[str, Any] = {
    "rows": [],
    "columns": [],
    "schema": {},
    "filename": "edited.parquet",
}

# ── helpers ────────────────────────────────────────────────────────────────
def _serialize(v: Any) -> Any:
    if v is None: return None
    if isinstance(v, bool): return v
    if isinstance(v, (int, float, str)): return v
    if hasattr(v, "item"): return v.item()
    if isinstance(v, bytes): return v.decode("utf-8", errors="replace")
    if isinstance(v, (datetime.date, datetime.datetime)): return v.isoformat()
    return str(v)

def _sql_val(v: Any) -> str:
    if v is None or v == "": return "NULL"
    if isinstance(v, bool): return "1" if v else "0"
    if isinstance(v, (int, float)): return str(v)
    escaped = str(v).replace("'", "''")
    return f"'{escaped}'"

# ── API routes ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return HTML, 200, {"Content-Type": "text/html; charset=utf-8"}

@app.route("/api/parse", methods=["POST"])
def api_parse():
    f = request.files.get("file")
    if not f: return jsonify({"error": "No file uploaded"}), 400

    buf = io.BytesIO(f.read())
    try:
        table = pq.read_table(buf)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400

    schema = [{"name": field.name, "type": str(field.type)} for field in table.schema]
    rows: list[dict] = []
    
    for batch in table.to_batches(max_chunksize=5000):
        d = batch.to_pydict()
        n = len(next(iter(d.values())))
        for i in range(n):
            rows.append({col: _serialize(d[col][i]) for col in d})

    _store["rows"]     = rows
    _store["columns"]  = [s["name"] for s in schema]
    _store["schema"]   = {s["name"]: s["type"] for s in schema}
    _store["filename"] = f.filename

    return jsonify({"columns": schema, "total": len(rows)})

@app.route("/api/data", methods=["GET"])
def api_get_data():
    page = int(request.args.get('page', 0))
    limit = int(request.args.get('limit', 50))
    search = request.args.get('search', '').lower()

    # Filter rows if search query exists
    filtered_rows = []
    for i, row in enumerate(_store["rows"]):
        if search:
            if not any(search in str(v).lower() for v in row.values() if v is not None):
                continue
        r = dict(row)
        r["_idx"] = i  
        filtered_rows.append(r)
        
    start = page * limit
    end = start + limit
        
    return jsonify({"rows": filtered_rows[start:end], "total": len(filtered_rows)})

@app.route("/api/data", methods=["POST"])
def api_add_row():
    new_row = {c: None for c in _store["columns"]}
    _store["rows"].insert(0, new_row)
    return jsonify({"success": True})

@app.route("/api/data/<int:idx>", methods=["PUT"])
def api_update_row(idx):
    col = request.json.get("column")
    val = request.json.get("value")
    
    if val == "":
        val = None
    else:
        try:
            if "." in val: val = float(val)
            else: val = int(val)
        except (ValueError, TypeError):
            pass

    _store["rows"][idx][col] = val
    return jsonify({"success": True})

@app.route("/api/data/<int:idx>", methods=["DELETE"])
def api_delete_row(idx):
    _store["rows"].pop(idx)
    return jsonify({"success": True})

# NEW ROUTE: Instantly save the file locally
@app.route("/api/save_local", methods=["POST"])
def api_save_local():
    try:
        tbl = pa.Table.from_pylist(_store["rows"])
        # Save to the folder where the python script is running
        save_path = os.path.join(os.getcwd(), _store["filename"])
        pq.write_table(tbl, save_path)
        return jsonify({"success": True, "path": save_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export/<fmt>")
def api_export(fmt):
    if fmt == "parquet":
        try:
            tbl = pa.Table.from_pylist(_store["rows"])
            buf = io.BytesIO()
            pq.write_table(tbl, buf)
            buf.seek(0)
            return send_file(buf, mimetype="application/octet-stream", as_attachment=True, download_name=f"edited_{_store['filename']}")
        except Exception as e:
            return str(e), 500
            
    elif fmt == "json":
        payload = json.dumps(_store["rows"], indent=2, default=str)
        return send_file(io.BytesIO(payload.encode()), mimetype="application/json", as_attachment=True, download_name="edited.json")
        
    elif fmt == "sql":
        tbl_name = _store["filename"].split(".")[0].replace(" ", "_")
        lines: list[str] = []
        for row in _store["rows"]:
            cols = list(row.keys())
            vals = ", ".join(_sql_val(row[c]) for c in cols)
            lines.append(f"INSERT INTO {tbl_name} ({', '.join(cols)}) VALUES ({vals});")
        return send_file(io.BytesIO("\n".join(lines).encode()), mimetype="text/plain", as_attachment=True, download_name="edited.sql")

# ── embedded UI ────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Parquet Admin Editor</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f0f2f7;--surface:#fff;--border:#dde1ea;--border-hover:#b0b8cc;
  --primary:#2c3e7a;--primary-light:#eef1fb;
  --text:#1a2035;--text2:#5a6380;--text3:#9aa0b4;
  --radius:10px;--radius-sm:6px;
  --shadow:0 2px 12px rgba(0,0,0,.06);
}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:var(--bg);color:var(--text);min-height:100vh;font-size:14px}

.hdr{background:var(--primary);color:#fff;padding:0 2rem;
  display:flex;align-items:center;justify-content:space-between;height:54px;
  box-shadow:0 2px 8px rgba(0,0,0,.18)}
.hdr-brand{display:flex;align-items:center;gap:10px;font-size:15px;font-weight:600}
.hdr-icon{width:28px;height:28px;background:rgba(255,255,255,.15);
  border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:16px}
.hdr-file{font-size:12px;color:rgba(255,255,255,.6);display:flex;align-items:center;gap:8px}
.hdr-file span{color:rgba(255,255,255,.9);font-weight:500}

.main{max-width:1200px;margin:0 auto;padding:1.5rem 1rem 3rem}

.stepper{display:flex;align-items:center;margin-bottom:1.5rem;
  background:var(--surface);border-radius:var(--radius);border:1px solid var(--border);
  padding:0 1rem;box-shadow:var(--shadow)}
.s-step{display:flex;align-items:center;gap:8px;padding:14px 12px;
  cursor:default;flex:1;border-bottom:2px solid transparent;transition:border-color .2s}
.s-step.active{border-bottom-color:var(--primary)}
.s-step.done{border-bottom-color:#4caf82}
.s-num{width:22px;height:22px;border-radius:50%;border:1.5px solid var(--border-hover);
  display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;
  color:var(--text2);flex-shrink:0}
.s-step.active .s-num{background:var(--primary);color:#fff;border-color:var(--primary)}
.s-step.done .s-num{background:#4caf82;color:#fff;border-color:#4caf82}
.s-label{font-size:13px;color:var(--text2);font-weight:500}
.s-step.active .s-label{color:var(--primary);font-weight:600}
.s-step.done .s-label{color:#2a7a52}
.s-div{width:1px;height:24px;background:var(--border);margin:0 4px}

.card{background:var(--surface);border-radius:var(--radius);border:1px solid var(--border);
  padding:1.5rem;box-shadow:var(--shadow);margin-bottom:1rem}

.dz{border:2px dashed var(--border-hover);border-radius:var(--radius);
  padding:4rem 2rem;text-align:center;cursor:pointer;transition:all .2s;background:var(--bg)}
.dz:hover,.dz.over{border-color:var(--primary);background:var(--primary-light)}
.dz-ico{font-size:40px;margin-bottom:14px;line-height:1}
.dz-title{font-size:16px;font-weight:600;color:var(--text);margin-bottom:6px}
.dz-sub{color:var(--text2);font-size:13px;margin-bottom:8px}
.btn-link{background:none;border:none;color:var(--primary);cursor:pointer;
  font-size:13px;text-decoration:underline;padding:0;font-family:inherit}
input[type=file]{display:none}

.btn{padding:8px 16px;border-radius:var(--radius-sm);font-size:13px;font-weight:500;
  cursor:pointer;font-family:inherit;transition:all .15s;border:1px solid transparent; display:flex; align-items:center; gap:6px;}
.btn-primary{background:var(--primary);color:#fff;border-color:var(--primary)}
.btn-primary:hover{background:#223060}
.btn-success{background:#2a7a52;color:#fff;border-color:#2a7a52}
.btn-success:hover{background:#1e5e3e}
.btn-secondary{background:var(--surface);color:var(--text);border-color:var(--border)}
.btn-secondary:hover{background:var(--bg)}

.export-bar{display:flex;align-items:center;gap:10px;margin-bottom:1rem;}
.spacer{flex:1;}

.search-input {padding: 8px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border); font-size: 13px; width: 300px; outline: none; transition: border-color 0.2s;}
.search-input:focus {border-color: var(--primary);}

.res-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:var(--radius-sm); max-height:600px;}
.res-tbl{width:100%;border-collapse:collapse;font-size:12px; font-family:'Menlo','Consolas',monospace}
.res-tbl th{text-align:left;padding:8px 10px;font-size:11px;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  font-weight:600;color:var(--text2);background:var(--bg);
  border-bottom:1px solid var(--border);white-space:nowrap;position:sticky;top:0; z-index:10;}
.res-tbl td{padding:6px 10px;border-bottom:1px solid var(--border);
  white-space:nowrap;max-width:200px;overflow:hidden;text-overflow:ellipsis;}
.res-tbl td[contenteditable="true"]{outline:none; cursor:text; transition: background .2s;}
.res-tbl td[contenteditable="true"]:focus{background:#fffbea; box-shadow: inset 0 0 0 2px #f0d070;}
.res-tbl td[contenteditable="true"]:hover{background:#fafbff;}
.res-tbl tr:last-child td{border-bottom:none}

.btn-del {background:#fff0f0; border:1px solid #f0b8b8; color:#a02020; cursor:pointer; padding:3px 8px; border-radius:4px; font-size:10px;}
.btn-del:hover {background:#ffd0d0;}

.pagination{display:flex; justify-content:center; align-items:center; gap:16px; margin-top:1rem; font-size:13px; color:var(--text2);}
</style>
</head>
<body>

<header class="hdr">
  <div class="hdr-brand"><div class="hdr-icon">⬡</div>Parquet CRUD Editor</div>
  <div class="hdr-file" id="hdr-file"></div>
</header>

<main class="main">
  <div class="stepper">
    <div class="s-step active" id="st1"><div class="s-num">1</div><div class="s-label">Upload Data</div></div>
    <div class="s-div"></div>
    <div class="s-step" id="st2"><div class="s-num">2</div><div class="s-label">Edit & Export</div></div>
  </div>

  <!-- Phase 1: Upload -->
  <div id="ph1" class="card">
    <div class="dz" id="dz">
      <div class="dz-ico">📂</div>
      <div class="dz-title">Drop a .parquet file here</div>
      <div class="dz-sub">or <button class="btn-link" id="btn-browse">browse files</button></div>
    </div>
    <input type="file" id="file-in" accept=".parquet,.parq">
  </div>

  <!-- Phase 2: Editor -->
  <div id="ph2" class="card" style="display:none">
    <div class="export-bar">
      <button class="btn btn-secondary" onclick="addRow()">➕ Add Row</button>
      <input type="text" id="search-box" class="search-input" placeholder="🔍 Search across all columns..." oninput="handleSearch()">
      
      <div class="spacer"></div>
      
      <!-- NEW LOCAL SAVE BUTTON -->
      <button class="btn btn-success" onclick="saveLocal()">💾 Save (Overwrite Local)</button>
      
      <button class="btn btn-primary" onclick="exportData('parquet')">⬇ Download Copy</button>
    </div>

    <div class="res-wrap">
      <table class="res-tbl">
        <thead><tr id="grid-head"></tr></thead>
        <tbody id="grid-body"></tbody>
      </table>
    </div>
    
    <div class="pagination">
      <button class="btn btn-secondary" onclick="prevPage()">← Prev</button>
      <span id="page-info">Page 1</span>
      <button class="btn btn-secondary" onclick="nextPage()">Next →</button>
    </div>
  </div>
</main>

<script>
const $ = id => document.getElementById(id);
let gState = { columns: [] };
let currentPage = 0;
const limit = 50;
let totalRows = 0;
let searchTimer = null;

// Upload Flow
const dz = $('dz'), fi = $('file-in');
$('btn-browse').onclick = () => fi.click();
dz.onclick = (e) => { if (e.target !== $('btn-browse')) fi.click(); };
fi.onchange = e => { if (e.target.files[0]) doUpload(e.target.files[0]); };
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('over');
  if (e.dataTransfer.files[0]) doUpload(e.dataTransfer.files[0]);
});

async function doUpload(file) {
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch('/api/parse', { method: 'POST', body: fd });
  const d = await r.json();
  if (r.ok) {
    gState.columns = d.columns;
    $('hdr-file').innerHTML = `<span>${file.name}</span>`;
    $('st1').className = 's-step done';
    $('st2').className = 's-step active';
    $('ph1').style.display = 'none';
    $('ph2').style.display = '';
    loadData();
  } else {
    alert(d.error || 'Upload failed');
  }
}

function handleSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => { currentPage = 0; loadData(); }, 300);
}

async function loadData() {
  const query = encodeURIComponent($('search-box').value || '');
  const r = await fetch(`/api/data?page=${currentPage}&limit=${limit}&search=${query}`);
  const d = await r.json();
  totalRows = d.total;
  renderGrid(d.rows);
}

function renderGrid(rows) {
  $('page-info').innerText = `Page ${currentPage + 1} (${totalRows.toLocaleString()} matches)`;
  $('grid-head').innerHTML = '<th style="width:50px; text-align:center;">Action</th>' + 
                             gState.columns.map(c => `<th>${c.name}</th>`).join('');

  if (rows.length === 0) {
     $('grid-body').innerHTML = `<tr><td colspan="${gState.columns.length + 1}" style="text-align:center; padding: 2rem; color: #9aa0b4;">No matching records found.</td></tr>`;
     return;
  }

  $('grid-body').innerHTML = rows.map(r => {
    return `<tr>
      <td style="text-align:center;"><button class="btn-del" onclick="deleteRow(${r._idx})">❌</button></td>
      ${gState.columns.map(c => {
        let val = r[c.name];
        val = (val === null || val === undefined) ? '' : val;
        let esc = String(val).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return `<td contenteditable="true" onblur="updateCell(${r._idx}, '${c.name}', this.innerText)">${esc}</td>`;
      }).join('')}
    </tr>`;
  }).join('');
}

async function updateCell(idx, col, val) {
  await fetch(`/api/data/${idx}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({column: col, value: val})
  });
}

async function deleteRow(idx) {
  if(!confirm("Are you sure you want to delete this row?")) return;
  await fetch(`/api/data/${idx}`, {method: 'DELETE'});
  loadData();
}

async function addRow() {
  $('search-box').value = ''; 
  await fetch(`/api/data`, {method: 'POST'});
  currentPage = 0; 
  loadData();
}

function prevPage() { if (currentPage > 0) { currentPage--; loadData(); } }
function nextPage() { if ((currentPage + 1) * limit < totalRows) { currentPage++; loadData(); } }

// --- Instant Save Logic ---
async function saveLocal() {
  const btn = event.target;
  const originalText = btn.innerText;
  btn.innerText = "⏳ Saving...";
  btn.disabled = true;

  try {
    const r = await fetch('/api/save_local', {method: 'POST'});
    const d = await r.json();
    if (r.ok && d.success) {
      alert(`✅ Saved successfully to:\n${d.path}\n\nYou can keep editing!`);
    } else {
      alert('❌ Error saving: ' + d.error);
    }
  } catch (e) {
    alert('❌ Network error: ' + e.message);
  } finally {
    btn.innerText = originalText;
    btn.disabled = false;
  }
}

function exportData(fmt) { window.location = `/api/export/${fmt}`; }
</script>
</body>
</html>"""

# ── entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PORT = 5500
    banner = f"""
  ╔══════════════════════════════════════╗
  ║       Parquet CRUD Editor            ║
  ╠══════════════════════════════════════╣
  ║  URL  →  http://localhost:{PORT}       ║
  ║  Stop →  Ctrl + C                    ║
  ╚══════════════════════════════════════╝
"""
    print(banner)
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)