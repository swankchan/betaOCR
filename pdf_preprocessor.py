# =====================================================================
# 檔案名稱：pdf_preprocessor.py
# 用途描述：PDF 智能預處理線路（純文字直出 / 掃描件自動轉 200 DPI 圖片）
# 
# [Program Spec]
# Input Parameters:
#   - pdf_path (str): 實體 PDF 檔案的讀取路徑
#   - output_image_dir (str, 預設為 None): 圖片輸出的資料夾。若為 None 則自動讀取環境變量
#   - 依賴環境變量 (.env): 
#       * PDF_DPI: 轉圖時的解析度 (預設 200)
#       * OUTPUT_IMAGE_DIR: 預設圖片暫存目錄 (預設 "output_images")
# Output Parameters:
#   - results (dict): 鍵為頁碼(int)，值為包含類型、文字內容與圖片路徑的字典群
#     格式範例：{ 1: {"type": "text", "content": "...", "image_path": None} }
# =====================================================================
import os
import fitz  # PyMuPDF
from dotenv import load_dotenv

# 啟動時自動載入 .env 配置
load_dotenv()

def preprocess_pdf(pdf_path: str, output_image_dir: str = None) -> dict:
    """
    檢查 PDF 每頁是否為純文字。
    如果是純文字直接提取；如果是掃描件，則自動轉為指定 DPI 的圖片。
    """
    # 如果呼叫時冇指定路徑，就全自動由 .env 讀取，再冇就 fallback 去 "output_images"
    if output_image_dir is None:
        output_image_dir = os.getenv("OUTPUT_IMAGE_DIR", "output_images")
        
    # 從 .env 讀取 DPI 設定，預設為 200
    pdf_dpi = int(os.getenv("PDF_DPI", "200"))
        
    if not os.path.exists(output_image_dir):
        os.makedirs(output_image_dir)
        
    results = {}
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    print(f"📖 開始預處理 PDF: {pdf_path} (DPI 設定: {pdf_dpi})")
    
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    for page_num in range(total_pages):
        page = doc[page_num]
        page_idx = page_num + 1
        
        extracted_text = page.get_text().strip()
        
        if len(extracted_text) > 10:
            print(f"  📄 [第 {page_idx}/{total_pages} 頁] 檢測到純文字")
            results[page_idx] = {
                "type": "text",
                "content": extracted_text,
                "image_path": None
            }
        else:
            print(f"  📸 [第 {page_idx}/{total_pages} 頁] 判定為掃描件，開始轉圖...")
            
            # 使用來自 .env 的 DPI 計算縮放率
            zoom = pdf_dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            
            image_filename = f"{pdf_name}_page_{page_idx}.jpg"
            image_path = os.path.join(output_image_dir, image_filename)
            pix.save(image_path)
            
            results[page_idx] = {
                "type": "image",
                "content": None,
                "image_path": image_path
            }
            
    doc.close()
    return results