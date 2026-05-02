This README provides a comprehensive overview and user guide for the **Parquet CRUD Editor**, a specialized utility developed for data professionals who need to perform rapid, local modifications to Parquet datasets without complex ETL pipelines.

---

# Parquet CRUD Editor
**Streamlined Data Manipulation for Parquet Files**

The **Parquet CRUD Editor** is a lightweight, web-based administrative tool designed to provide a "spreadsheet-like" interface for Parquet files[cite: 1]. It allows for real-time data editing, searching, and local persistence, making it an ideal choice for Data Engineers and Analysts performing data cleaning or manual record updates.

## Key Features

*   **Interactive Data Grid**: Perform inline editing by clicking directly on any cell. Changes are updated in the application state instantly.
*   **Full CRUD Support**: 
    *   **Insert**: Add new rows to the top of the dataset.
    *   **Update**: Modify existing record values with automatic type coercion.
    *   **Delete**: Remove specific rows from the dataset with a single click.
*   **Global Search**: A debounced, real-time search bar that filters across all columns simultaneously to locate specific records quickly.
*   **Local Overwrite (Save)**: A "Save" function that writes modified data directly back to the local directory, bypassing the need for repeated browser downloads.
*   **Multi-Format Export**: Export the final dataset back to `.parquet`, or generate `SQL` (INSERT statements) and `JSON` versions for database migrations[cite: 1].

---

## Technical Architecture

The tool is built on a modern, "zero-config" stack designed to run locally on any machine with Python installed.

### Dependencies & Bootstrapping
The application includes a built-in dependency manager that checks for and installs required libraries upon execution[cite: 1]:
*   **Flask**: Powers the web server and API routing[cite: 1].
*   **PyArrow**: Handles the heavy lifting of reading, writing, and manipulating Parquet tables[cite: 1].

### Workflow
1.  **File Parsing**: The tool reads the `.parquet` file into a PyArrow Table and converts it to a Python list of dictionaries for the UI[cite: 1].
2.  **Schema Awareness**: It automatically detects column names and data types (e.g., `int64`, `string`, `double`) from the Parquet metadata[cite: 1].
3.  **In-Memory State**: Edits are held in an in-memory store until a "Save" or "Export" command is triggered.

---

## Quick Start Guide

### 1. Prerequisites
Ensure you have **Python 3.8+** installed. No manual `pip install` commands are required for the primary dependencies.

### 2. Execution
Run the script from your terminal:
```bash
python admin.py
```

### 3. Usage Steps
*   **Upload**: Drag and drop your `.parquet` file into the browser window[cite: 1].
*   **Search**: Use the search bar to narrow down the rows you wish to edit.
*   **Edit**: Click on any value to modify it. Changes are captured when you click away (on blur).
*   **Save**: Click **"Save (Overwrite Local)"** to apply your changes directly to the file in your current folder.

---

## Technical Details for Engineers

| Feature | Description |
| :--- | :--- |
| **Data Handling** | Uses `pyarrow.parquet` for high-performance I/O[cite: 1]. |
| **Port Configuration** | Defaults to `http://localhost:5500`[cite: 1]. |
| **SQL Generation** | Creates standard `INSERT INTO` statements based on the filename[cite: 1]. |
| **JSON Export** | Formats data as an array of objects, preserving ISO dates[cite: 1]. |

> **Note**: The tool currently saves the file to the current working directory (`os.getcwd()`) using the original filename when the "Save" function is triggered.

---

**Developed by CL Magno I.T. Solutions**
*Precise code. Clear explanations.*

Does this README cover everything you need for your learning portal, or would you like to add a specific section on the PyArrow schema handling?