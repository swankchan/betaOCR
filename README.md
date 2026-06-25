# 📄 智能月結單 OCR 數據提取系統 (AI Bank Statement OCR Extractor)

這是一套工業落地感極強、採用 **FPES (Frontend-Preprocessor-Engine-Schema)** 四層分工架構的智能金融月結單結構化提取系統。系統專為本地運行大模型（如 `llama.cpp` + `Qwen3-VL-8B-Instruct`）與高規格硬體（如 **NVIDIA DGX Spark / Intel Arc**）進行深度極致優化，具備非同步高併發、金融級鋼鐵防禦盾與隨身 Portable 部署能力。

---

## 🛠️ 系統核心架構 (FPES Framework)

整個系統數據流水線（Pipeline）分工極其明確，具備強大的防禦性編程智慧：

1. **Frontend (Streamlit 2026)**：提供寬度自適應（`width='stretch'`）的 Web 介面，內置真實掛鐘總耗時器與 `asyncio.as_completed` 動態刷新進度條。
2. **Preprocessor (PyMuPDF)**：智能雙軌分流。純文字頁面直接秒級提取；掃描/陰影頁自動轉為高精度 200 DPI 圖片，兼顧速度與 Token 成本。
3. **Engine (llama.cpp Async Client)**：封裝 `AsyncOpenAI` 進行多頁面並發齊發，注入 12B 高級大腦分頁上下文防禦提示詞。
4. **Schema (Pydantic / Instructor)**：強制型態鎖死（Type Locking）與外幣雙星解耦（金額與幣別分離），在 C++ 底層啟用 GBNF 語法鎖（Grammar Constraint）。

---

## 🌟 核心技術亮點

* ⚡ **Async 高併發齊發機制**：利用 `asyncio.gather` 與信號量（`Semaphore`）控制並發水龍頭，徹底榨乾 GPU 算力。
* 🛡️ **金融級精準度防禦盾**：
  * `temperature=0.0`、`top_p=0.1`、`repeat_penalty=1.0` 鎖死模型隨機創造力，杜絕數字抄寫幻覺。
  * 強制注入 `response_format` 觸發 `llama.cpp` 原生 GBNF 語法鎖，大模型絕不吐出格式崩潰的 JSON。
* 📊 **Pandas 數據清洗盾**：前端強制利用 `pd.to_numeric(errors='coerce')` 進行二次對齊清洗，徹底封鎖 Apache Arrow 陰陽界混合型態報錯。
* ⏱️ **總體真實掛鐘耗時指標**：前端展示總處理時間，幫助在不同硬體平台上精準評估 `--parallel` 與 `sem` 的最優解。

---

## 📁 隨身 USB 手指 (Portable) 部署秘籍 ——「Z 碟鐵律」

本系統支持完全裝入高速 USB 手指，周圍去不同硬件平台進行極速 Demo，避開 Conda 絕對路徑陷阱的步驟如下：

1. **變更磁碟機代號**：插上 USB 手指，進入 Windows「磁碟管理」，將手指盤符硬性修改為 **`Z:`** 碟。
2. **部署環境**：將 `Git Portable`、`Miniconda3` 悉數安裝在 `Z:\` 根目錄下。在隨身 Python 環境中裝妥 Streamlit、Pandas、Pydantic。
3. **模型預載**：將高精度量化模型（如 `Qwen2.5-VL-7B-Instruct-Q8_0.gguf` 或 `f16`）直接存放在 `Z:\AI_OCR_Project\models\`。
4. **一鍵啟動**：去到任何全新客戶電腦，將手指改為 `Z:`，雙擊根目錄的 `demo.bat` 即可無縫復活整個 Python 網頁環境。

---

## 🚀 生產環境 (Production) 部署與運行指南

### 1. 設置環境變量 (`.env`)
在專案根目錄下建立 `.env` 檔案並配置：
```env
OPENAI_API_KEY=no-key
OPENAI_BASE_URL=http://localhost:8080/v1
LLM_MODEL=qwen3-vl-8b-instruct
LLM_NUM_CTX=32768
INPUT_PDF_DIR=input_pdfs
OUTPUT_IMAGE_DIR=output_pages
OUTPUT_DATA_DIR=output_json
PDF_DPI=200