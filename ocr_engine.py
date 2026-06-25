# =====================================================================
# 檔案名稱：ocr_engine.py
# 用途描述：流派一完全體 — 12B 權威提示詞與分頁防禦，升級 Async 非同步引擎
# =====================================================================
import os
import base64
import instructor
from openai import AsyncOpenAI  # 🎯 變更 1：從 OpenAI 改為引進 AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

from schemas import BankStatement

def encode_image_to_base64(image_path: str) -> str:
    """將本地磁碟上的圖片轉為 Base64 字串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# 🎯 變更 2：在函數前面加上 async 關鍵字（建議改名加上 _async 方便 app.py 識別）
async def extract_data_with_llm_async(page_type: str, text_content: str = None, image_path: str = None) -> BankStatement:
    """
    調用大模型進行結構化數據提取，強制要求輸出符合鋼鐵流派一契約。（非同步版）
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model_name = os.getenv("LLM_MODEL")
    num_ctx = int(os.getenv("LLM_NUM_CTX", "16384"))
    
    # 🎯 變更 3：將實例化客戶端改為 AsyncOpenAI
    raw_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    client = instructor.from_openai(raw_client, mode=instructor.Mode.JSON)
    
    # 🎯 注入 12B 高級大腦專用權威指令 (保持你原本強大的 Prompt 不變)
    system_instruction = (
        "你是一個專業的金融審計專家。請精確提取輸入頁面中的月結單數據。\n\n"
        "請注意,你處理的月結單格式不一,排序不一,所以要理解清楚, 而且, 外幣可能留空, 但港幣一定會有, 小心對錯位置.\n\n"
        "💡 【分頁處理重要告示】 💡\n"
        "目前輸入的只是整份文件中的【其中一頁】。如果當前頁面頂部沒有基礎資料，"
        "請直接將對應基礎欄位設為 null，立刻專注去提取當前頁面的交易明細表格（transactions）！\n\n"
        "表格每行的內容包括(名稱因不同銀行可能有異, 排序也沒有固定):1.交易日期, 2. 結算日期, 3. 內容明細, 4. 外幣金額及種類(如有), 5. 港幣金額.] 部份內容也可能結合及同一個欄位.\n"
        "🌟 數字清洗與型態鐵律 🌟：\n"
        "1. 所有金額欄位輸出時，絕對不能包含千分位逗號（,）或任何貨幣符號（$）。12B大腦請自行將其去掉！\n"
        "2. 對於常規本地港幣交易，外幣相關欄位請全部填 null，港幣金額填入 `amount_hkd`（必須保留原始負號，如 -103.00）。\n"
        "3. 對於外幣交易（例如原文出現 'USD 12.50' 或 '7.50 GBP'）：\n"
        "   - 你必須把數字部分洗乾淨，填入 `foreign_currency_amount`（純浮點數，如 12.50）。\n"
        "   - 你必須把幣別部分提取出來，填入 `foreign_currency_code`（三位大寫字母，如 'USD'、'GBP'）。\n"
        "   - 同時，行尾的港幣結算金額依然要老老實實填入 `amount_hkd`。"
    )
    
    messages = [{"role": "user", "content": [{"type": "text", "text": system_instruction}]}]
    
    if page_type == "text":
        messages[0]["content"].append({"type": "text", "text": f"以下是當前頁面的純文字數據：\n\n{text_content}"})
    elif page_type == "image":
        base64_image = encode_image_to_base64(image_path)
        messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

    # 🎯 變更 4：在真正發送請求的 client 前面加上 await 關鍵字
    structured_output = await client.chat.completions.create(
        model=model_name, 
        response_model=BankStatement, 
        # 🎯 核心防禦：強制通知 llama.cpp 啟用 native strict json mode
        response_format={"type": "json_object", "schema": BankStatement.model_json_schema()},
        messages=messages,
        temperature=0.0,
        max_tokens=8192,
        extra_body={
            "options": {
                "num_ctx": num_ctx,
                "num_predict": 8192,
                "top_p": 0.1,      # 🎯 壓低 Top_P，進一步鎖死確定性
                "repeat_penalty": 1.0 # 🎯 設為 1.0，防止惩罚機制破壞相同的數字（如 0.00）
            }
        }
    )
    return structured_output