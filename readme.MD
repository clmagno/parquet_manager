# Parquet Admin Tool

A lightweight browser-based admin tool for loading Parquet files and
configuring INSERT / UPDATE / DELETE operations per column.

---

## Quick start

### Option A — Auto-install (recommended)
```
python admin.py
```
The script detects and installs `flask` and `pyarrow` automatically on first run.

### Option B — Manual install
```
pip install -r requirements.txt
python admin.py
```

The browser opens automatically at **http://localhost:5500**.  
Press **Ctrl + C** in the terminal to stop the server.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10 or higher |
| flask | 3.0+ |
| pyarrow | 15.0+ |

---

## How it works

### Step 1 — Upload
Drag-and-drop or browse for any `.parquet` file.  
The file is parsed server-side with PyArrow for full type support.

### Step 2 — Configure
For each column choose:
- **INSERT** — include this column when inserting new records  
- **UPDATE** — include this column in UPDATE SET clauses  
- **Exclude** — omit the column from all operations  

Then set:
- **Primary key column** — identifies whether a row is new (INSERT) or existing (UPDATE)
- **Delete-flag column + value** — any row where this column equals the value becomes a DELETE
- **Existing IDs** — paste known IDs (comma- or newline-separated) to trigger UPDATE logic

### Step 3 — Results
Preview up to 300 rows with colour-coded operation badges, filter by op type, then export:
- **JSON** — full structured array of operations
- **SQL** — ready-to-run INSERT / UPDATE / DELETE statements (edit `your_table` name in the UI)

---

## Packaging into a single executable (optional)

```
pip install pyinstaller
pyinstaller --onefile admin.py
```

The resulting `dist/admin` (or `.exe` on Windows) runs without Python installed.

---

## Notes

- All processing is local — no data is sent anywhere.
- The preview table shows up to 300 rows; exports contain all rows.
- Large files (millions of rows) may take a few seconds to parse.