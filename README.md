[ PDF Statement ] 
       │
       ▼
 1. 輕量本地預處理 (使用 PyMuPDF / pdfplumber)
    ├── 檢查是否是純文字 PDF (Text-based) ➔ 直接提取文字
    └── 如果是掃描件 (Scanned PDF) ➔ 將頁面轉為 200 DPI 圖片
       │
       ▼
 2. 頁面過濾 (Page Router)
    └── 很多 Statement 有 10 頁，但只有前 2 頁有交易紀錄。
        用一個極便宜的小模型，先盲猜哪幾頁有表格，只將這幾頁丟給大模型。
       │
       ▼
 3. 核心 VLM 視覺提取 (例如 Claude 3.5 Sonnet / Qwen3.5-VL)
    └── 配合 Structured Outputs (JSON Mode / Pydantic)
       │
       ▼
[ 100% 完美的結構化 JSON 數據 ]