Here is the updated, professionally formatted README for your **Parquet CRUD Editor**. It is designed to be copy-paste ready and includes the specific screenshots and features you've implemented.

***

# Parquet CRUD Editor
**A Professional Data Manipulation Utility for Engineers & Analysts**

The **Parquet CRUD Editor** is a lightweight, web-based administrative tool designed to provide a "spreadsheet-like" interface for Parquet files[cite: 1]. It empowers Data Engineers and Analysts to perform rapid, manual modifications to datasets without the overhead of complex ETL pipelines or notebook environments.

---

## 📸 Screenshots

### Step 1: Secure Local Upload
Drag-and-drop your `.parquet` files directly into the browser. Processing happens entirely on your local machine.

![Secure Local Upload](https://drive.google.com/uc?export=view&id=1Cl5HVUAaNXBRfWO44NnZlYRQ5tbKBhr0)

### Step 2: Interactive Data Grid
A full-featured editor with global search, inline cell editing, and instant local saving.

![Interactive Data Grid](https://drive.google.com/uc?export=view&id=1RQ7HqrNvqTnsFKfz35BLAOfMK2WCwjb_)

---

## 🚀 Key Features

*   **Interactive Inline Editing**: Click any cell to modify values instantly. The application handles type coercion (integers, floats, strings) automatically[cite: 1].
*   **Full CRUD Support**:
    *   **Add Row**: Inject new, empty records at the top of your dataset[cite: 1].
    *   **Delete**: Remove specific records with a single click[cite: 1].
*   **💾 Save (Overwrite Local)**: **(New)** Overwrite the source file directly in your working directory, allowing for an "instant refresh" workflow without repeated downloads[cite: 1].
*   **🔍 Global Search**: A high-performance, debounced search bar that filters across all columns simultaneously as you type[cite: 1].
*   **⬇️ Multi-Format Export**: Download modified data as a new `.parquet` file, or export to `SQL` (INSERT statements) and `JSON`[cite: 1].

---

## 🛠 Technical Architecture

The tool is built on a "zero-configuration" stack, designed to be portable and efficient.

### Dependencies
The script includes an auto-bootstrap feature that ensures all requirements are met upon execution[cite: 1]:
*   **Flask**: Lightweight web server for the UI and API[cite: 1].
*   **PyArrow**: High-performance library for reading, writing, and manipulating Parquet tables[cite: 1].

### Internal Logic
1.  **State Management**: Modified rows are held in a secure in-memory store (`_store`) to ensure fast UI performance[cite: 1].
2.  **Schema Retention**: The tool detects and preserves the original column schema and data types from the source file metadata[cite: 1].

---

## 📖 Quick Start Guide

### 1. Prerequisites
Ensure you have **Python 3.8+** installed.

### 2. Execution
Run the script from your terminal:
```bash
python admin.py
```

### 3. Usage Steps
*   **Upload**: Drag your file into the Step 1 area[cite: 1].
*   **Edit**: Use the search bar to find a record, then click a cell to change its value[cite: 1].
*   **Sync**: Click **"Save (Overwrite Local)"** to apply changes directly to your file instantly[cite: 1].

---

## 📑 Technical Summary

| Feature | Specification |
| :--- | :--- |
| **Backend** | Python 3.x / Flask[cite: 1] |
| **Engine** | Apache Arrow (PyArrow)[cite: 1] |
| **I/O Operations** | Local file system overwrite support[cite: 1] |
| **UI** | Embedded HTML/JavaScript with CSS Variables[cite: 1] |

---

**Developed by CL Magno I.T. Solutions**  
*Precise code. Clear explanations.*
