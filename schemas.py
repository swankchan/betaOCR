# =====================================================================
# 檔案名稱：schemas.py
# 用途描述：流派一完全體 — 全線鎖死純數字，外幣欄位完美解耦 (支援 12B 旗艦模型)
# =====================================================================
from typing import List, Optional
from pydantic import BaseModel, Field

class MoxTransactionItem(BaseModel):
    activity_date: str = Field(description="交易日期/活動日期，例如 '27 Apr'")
    settlement_date: str = Field(description="結算日期，例如 '29 Apr'")
    description: str = Field(description="商戶名稱或交易詳情描述")
    
    # 🎯 外幣拆雙星組合：一個純數字 (float)，一個純代碼 (str)
    foreign_currency_amount: Optional[float] = Field(
        default=None, 
        description="外幣原始金額數字。必須為純浮點數數字（如 12.50 或 10000.00）。"
                    "注意：千萬不要包含千分位逗號（,）或貨幣符號。若無外幣交易則必須填 null。"
    )
    foreign_currency_code: Optional[str] = Field(
        default=None, 
        description="外幣幣別代碼，必須為三位大寫英文字母，例如 'USD', 'JPY', 'EUR', 'GBP'。若無外幣交易則必須填 null。"
    )
    
    # 🎯 港幣金額同樣硬性鎖死 float
    amount_hkd: float = Field(
        description="港幣金額 (Amount (HKD))。必須為純浮點數（數字），嚴格保留原始正負號（如 -103.00）。"
                    "注意：千萬不要包含千分位逗號（,）或任何貨幣符號。"
    )

class BankStatement(BaseModel):
    bank_name: Optional[str] = Field(default="Mox Bank", description="銀行名稱")
    account_holder_name: Optional[str] = Field(default=None, description="持有人英文姓名（若當前頁面找不到則填 null）")
    statement_period: Optional[str] = Field(default=None, description="月結單結算週期（若當前頁面找不到則填 null）")
    total_credit_limit: Optional[float] = Field(default=None, description="總信貸額度（若當前頁面找不到則填 null）")
    statement_balance: Optional[float] = Field(default=None, description="月結單當期總結餘（若當前頁面找不到則填 null）")
    minimum_amount_due: Optional[float] = Field(default=None, description="最低還款額（若當前頁面找不到則填 null）")
    payment_due_date: Optional[str] = Field(default=None, description="到期繳款日 (YYYY-MM-DD)（若當前頁面找不到則填 null）")
    transactions: List[MoxTransactionItem] = Field(default=[], description="當前頁面提取到的交易明細清單")