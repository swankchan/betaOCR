# =====================================================================
# 檔案名稱：app.py
# 用途描述：智能月結單 OCR 前端主程式 - 支援【Async 非同步全頁面並行提取】與本地備份 (流派一完全體)
# 
# [Program Spec]
# Input Parameters:
#   - 依賴環境變量 (.env): INPUT_PDF_DIR, OUTPUT_IMAGE_DIR, OUTPUT_DATA_DIR, LLM_MODEL
#   - 用戶 UI 輸入: 網頁下拉選單選擇之 PDF，或手動上傳之 PDF 檔案流
# Output Parameters:
#   - nil (直接將結果渲染至網頁 UI，無程式傳回值)
# =====================================================================
import os
import asyncio  # 🎯 新增：引進 Python 標準非同步庫
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import time

load_dotenv()

from pdf_preprocessor import preprocess_pdf
# 🎯 變更：改為引入非同步版本的 LLM 提取函數
from ocr_engine import extract_data_with_llm_async 
from schemas import BankStatement

# =====================================================================
# 🎯 核心非同步調度引擎 (Parallel Orchestrator)
# =====================================================================
async def process_all_pages_async(pdf_summary: dict, progress_bar) -> dict:
    """
    非同步核心調度器：利用 asyncio 全頁面並發齊發，並保持 Streamlit 進度條動態刷新。
    """
    # 🛡️ 工業級防禦：設定最大併發數為 5，既能享受數倍飆速，又能防範衝破大模型 API 的 Rate Limit
    sem = asyncio.Semaphore(1)
    
    async def extract_page_worker(page_idx, page_data):
        async with sem:  # 透過信號量鎖定最大併發
            start_time = time.time()  # ⏳ 開始計時
            if page_data["type"] == "text":
                res = await extract_data_with_llm_async(
                    page_type="text", 
                    text_content=page_data["content"]
                )
            else:
                res = await extract_data_with_llm_async(
                    page_type="image", 
                    image_path=page_data["image_path"]
                )
            elapsed = time.time() - start_time  # ⏳ 計算耗時
            print(f"⏱️ [Page {page_idx}] 提取完成，耗時 {elapsed:.2f} 秒 (類型: {page_data['type']})")
        return page_idx, res

    # 建立所有頁面的非同步協程任務群
    tasks = [extract_page_worker(pidx, pdata) for pidx, pdata in pdf_summary.items()]
    results_map = {}
    total_pages = len(tasks)
    
    # 🎯 奇蹟時刻：使用 as_completed 哪一頁先好就先處理，完美驅動進度條
    for idx, completed_task in enumerate(asyncio.as_completed(tasks)):
        page_idx, page_result = await completed_task
        results_map[page_idx] = page_result
        # 即時刷新前端進度條
        progress_bar.progress((idx + 1) / total_pages)
        
    return results_map


def main():
    st.set_page_config(page_title="智能月結單 OCR 提取器", page_icon="📄", layout="wide")
    
    st.title("📄 智能月結單 OCR 數據提取器")
    st.write("已成功將 **Async 非同步高併發齊發與流派一防禦盾** 部署上線。")
    st.markdown("---")
    
    input_dir = os.getenv("INPUT_PDF_DIR", "input_pdfs")
    conf_output_dir = os.getenv("OUTPUT_IMAGE_DIR", "output_pages")
    output_json_dir = os.getenv("OUTPUT_DATA_DIR", "output_json")
    
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
    
    st.sidebar.header("⚙️ 當前環境配置")
    st.sidebar.text(f"📁 輸入目錄: {input_dir}/")
    st.sidebar.text(f"🎬 運行模型: {os.getenv('LLM_MODEL')}")
    st.sidebar.text(f"📸 轉圖目錄: {conf_output_dir}/")
    
    local_pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    tab1, tab2 = st.tabs(["📁 方案 A：從本地資料夾選取", "📤 方案 B：手動上傳新檔案"])
    target_pdf_path = None
    
    with tab1:
        if len(local_pdf_files) == 0:
            st.warning(f"💡 目前 `./{input_dir}` 資料夾內空空如也。")
        else:
            selected_file = st.selectbox("請選擇要分析的月結單檔案：", local_pdf_files)
            if selected_file:
                target_pdf_path = os.path.join(input_dir, selected_file)
                st.info(f"📍 已鎖定本地檔案: `{target_pdf_path}`")
                
    with tab2:
        uploaded_file = st.file_uploader("手動拖放上傳 PDF", type=["pdf"])
        if uploaded_file is not None:
            temp_path = f"temp_upload_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            target_pdf_path = temp_path
            st.info(f"📍 已鎖定上傳檔案: `{uploaded_file.name}`")

    st.markdown("---")
    
    if target_pdf_path and st.button("🚀 開始進行多頁全自動數據提取", type="primary"):
        
        # 階段 1：調用預處理模組剖析所有頁面
        with st.spinner("🔍 階段 1: 正在進行本地預處理分流..."):
            pdf_summary = preprocess_pdf(target_pdf_path, output_image_dir=conf_output_dir)
        
        # 階段 2：發動 Async 非同步任務齊發，進行多輪提取
        with st.spinner("⚡ 階段 2: 核心 Async 引擎啟動！正在全頁面同時傳輸、高開高打提取中..."):
            try:
                total_start_time = time.time()  # ⏳ 1. 記錄整份文件提取的起跑時間

                # 建立 Streamlit 頁面進度條
                progress_bar = st.progress(0)
                total_pages = len(pdf_summary)
                
                # 🎯 呼叫非同步事件循環 (Event Loop) 來執行調度引擎
                results_map = asyncio.run(process_all_pages_async(pdf_summary, progress_bar))
                
                # ⏳ 2. 計算整份文件從齊發到全部收工的「真實總體耗時」
                total_elapsed_time = time.time() - total_start_time
                # 同步打印到後台 Console 方便你做運維壓測
                print(f"\n==================================================")
                print(f"🚀 [📊 壓測報告] 整份 PDF 處理完成！")
                print(f"   - 總處理頁數: {total_pages} 頁")
                print(f"   - 核心總體耗時 (Wall Time): {total_elapsed_time:.2f} 秒")
                print(f"==================================================\n")

                # 任務全部完成後，開始進行結構串聯與合體
                final_result = None
                aggregated_transactions = []
                
                # 依照正確頁碼順序進行主幹與流水線的合龍
                for page_idx in sorted(results_map.keys()):
                    page_result = results_map[page_idx]
                    
                    # 如果是第一頁，將其選定為主體架構（用作保留銀行和用戶基本資料）
                    if page_idx == 1:
                        final_result = page_result
                        
                    # 收集每一頁抽取出來的交易明細
                    if page_result and page_result.transactions:
                        aggregated_transactions.extend(page_result.transactions)
                
                # 核心合體：將所有頁面收集到的明細，強行灌回主結構中
                if final_result:
                    final_result.transactions = aggregated_transactions
                
                # 階段 3：網頁 UI 渲染呈現
                st.success(
                    f"🎉 全自動結構化提取完成！非同步併發成功處理共 {total_pages} 頁數據。\n\n"
                    f"⏱️ **【系統效能指標】總體真實耗時：`{total_elapsed_time:.2f}` 秒** "
                    f"(平均每頁耗時: `{total_elapsed_time/total_pages:.2f}` 秒)")
                st.markdown("---")
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.subheader("🏦 月結單核心基礎資料")
                    st.write(f"**發卡機構 / 銀行名稱:** {final_result.bank_name}")
                    st.write(f"**客戶持有人姓名:** {final_result.account_holder_name}")
                    st.write(f"**月結單結算週期:** {final_result.statement_period}")
                    st.write(f"**總信貸額度 (Credit Limit):** {final_result.total_credit_limit}")
                    st.write(f"**月結單總結餘 (Statement Balance):** {final_result.statement_balance}")
                    st.write(f"**最低還款額 (Minimum Due):** {final_result.minimum_amount_due}")
                    st.write(f"**到期繳款日 (Due Date):** {final_result.payment_due_date}")
                
                with col2:
                    st.subheader("📦 原生 JSON 數據")
                    st.json(final_result.model_dump())
                
                st.subheader("📊 智能提取的全體交易明細清單 (Transactions)")
                if final_result.transactions:
                    tx_list = [tx.model_dump() for tx in final_result.transactions]
                    df = pd.DataFrame(tx_list)
                    
                    # 🎯 【流派一防禦盾】將金額欄位強制轉換為純 float64 數值型態，徹底封鎖 Arrow 陰陽界報錯
                    if 'foreign_currency_amount' in df.columns:
                        df['foreign_currency_amount'] = pd.to_numeric(df['foreign_currency_amount'], errors='coerce')
                    if 'amount_hkd' in df.columns:
                        df['amount_hkd'] = pd.to_numeric(df['amount_hkd'], errors='coerce')
                    
                    # 防禦性措施：確保所有預期欄位皆存在，防範極特殊狀況下的 KeyError
                    expected_cols = ['activity_date', 'settlement_date', 'description', 'foreign_currency_amount', 'foreign_currency_code', 'amount_hkd']
                    for col in expected_cols:
                        if col not in df.columns:
                            df[col] = None
                    
                    # 🎯 【新對齊】選取並對齊新拆解出來的外幣雙星欄位
                    df = df[expected_cols]
                    df.columns = ['交易日期', '結算日期', '商戶與交易詳情描述', '外幣金額', '外幣幣別', '金額 (HKD)']
                    
                    # 使用最新的寬度自適應語法呈現網頁表格
                    st.dataframe(df, width='stretch')
                else:
                    st.warning("⚠️ 該文件未偵測到任何有效的交易流水明細。")

                # --- 自動儲存完整的 JSON 到本地磁碟 ---
                if not os.path.exists(output_json_dir):
                    os.makedirs(output_json_dir)

                base_name = os.path.splitext(os.path.basename(target_pdf_path))[0]
                base_name = base_name.replace("temp_upload_", "") 
                json_output_path = os.path.join(output_json_dir, f"{base_name}.json")

                with open(json_output_path, "w", encoding="utf-8") as f:
                    f.write(final_result.model_dump_json(indent=4))

                st.info(f"💾 備份成功：全量合併數據已自動落入 `./{json_output_path}`")

            except Exception as e:
                st.error(f"❌ 運行時發生錯誤: {e}")
            finally:
                if target_pdf_path.startswith("temp_upload_") and os.path.exists(target_pdf_path):
                    os.remove(target_pdf_path)

if __name__ == "__main__":
    main()