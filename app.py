# =====================================================================
# 檔案名稱：app.py
# 用途描述：智能月結單 OCR 前端主程式 - 支援全頁面流水自動循環合併與本地備份 (流派一完全體)
# 
# [Program Spec]
# Input Parameters:
#   - 依賴環境變量 (.env): INPUT_PDF_DIR, OUTPUT_IMAGE_DIR, OUTPUT_DATA_DIR, LLM_MODEL
#   - 用戶 UI 輸入: 網頁下拉選單選擇之 PDF，或手動上傳之 PDF 檔案流
# Output Parameters:
#   - nil (直接將結果渲染至網頁 UI，無程式傳回值)
# =====================================================================
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from pdf_preprocessor import preprocess_pdf
from ocr_engine import extract_data_with_llm
from schemas import BankStatement

def main():
    st.set_page_config(page_title="智能月結單 OCR 提取器", page_icon="📄", layout="wide")
    
    st.title("📄 智能月結單 OCR 數據提取器")
    st.write("已成功將 **全頁面流水自動循環合併機制** 部署上線。")
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
        with st.spinner("🔍 階段 1: 正在行本地預處理分流..."):
            pdf_summary = preprocess_pdf(target_pdf_path, output_image_dir=conf_output_dir)
        
        # 階段 2：遍歷所有頁面，發動多輪提取並進行流水線合併
        with st.spinner("🧠 階段 2: 核心 OCR 引擎正在逐頁提取並串聯流水帳..."):
            try:
                final_result = None
                aggregated_transactions = []
                
                # 建立 Streamlit 頁面進度條
                progress_bar = st.progress(0)
                total_pages = len(pdf_summary)
                
                for idx, page_idx in enumerate(sorted(pdf_summary.keys())):
                    st.text(f"⏳ 正在分析第 {page_idx} / {total_pages} 頁...")
                    page_data = pdf_summary[page_idx]
                    
                    # 呼叫大模型提取當前頁面
                    if page_data["type"] == "text":
                        page_result: BankStatement = extract_data_with_llm(
                            page_type="text", 
                            text_content=page_data["content"]
                        )
                    else:
                        page_result: BankStatement = extract_data_with_llm(
                            page_type="image", 
                            image_path=page_data["image_path"]
                        )
                    
                    # 如果是第一頁，將其選定為主體架構（用作保留銀行和用戶基本資料）
                    if page_idx == 1:
                        final_result = page_result
                        
                    # 收集每一頁抽取出來的交易明細
                    if page_result.transactions:
                        aggregated_transactions.extend(page_result.transactions)
                        
                    # 更新進度條
                    progress_bar.progress((idx + 1) / total_pages)
                
                # 核心合體：將所有頁面收集到的明細，強行灌回主結構中
                if final_result:
                    final_result.transactions = aggregated_transactions
                
                # 階段 3：網頁 UI 渲染呈現
                st.success(f"🎉 全自動結構化提取完成！成功合併處理共 {total_pages} 頁數據。")
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
                    st.dataframe(df, use_container_width=True)
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