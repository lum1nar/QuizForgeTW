import requests
import json
import pdfplumber
import re
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"

CHUNKED_LIST_FILE = "chunked_pdfs.json"
OUTPUT_FILE = "all_chunks.json"
PDF_DIR = "./pdf"

# ========================
# Load processed pdf list
# ========================
if os.path.exists(CHUNKED_LIST_FILE):
    with open(CHUNKED_LIST_FILE, "r", encoding="utf-8") as f:
        chunked_pdfs = set(json.load(f))
else:
    chunked_pdfs = set()

# ========================
# Scan PDF directory
# ========================
pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

print(f"📄 發現 {len(pdf_files)} 份 PDF")

def extract_text_by_page(pdf_path):
    """回傳每頁文字列表"""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # 移除中文與標點
                clean_text = re.sub(
                    r"[\u4e00-\u9fff，。！？【】（）《》；：]", "", text
                )
                pages_text.append(clean_text)
    return pages_text

def extract_json_objects_from_text(text):
    objects = []
    stack = []
    start = None

    for i, ch in enumerate(text):
        if ch == "{":
            if not stack:
                start = i
            stack.append("{")
        elif ch == "}":
            if stack:
                stack.pop()
                if not stack and start is not None:
                    obj_text = text[start : i + 1]
                    objects.append(obj_text)
                    start = None
    return objects

def generate_prompt(content, difficulty_level):
    return f"""
你是一個英文教學專家，並負責題目切分與結構化標註（chunking）系統。

【任務目標】
請將以下英文考卷內容切分為「可直接用於出題與 RAG 檢索」的 chunk。

【重要原則】
1. 一個 chunk 必須是「完整、不可拆分」的題單位。
2. 不可將同一題的題幹與選項拆到不同 chunk。
3. 克漏字與閱讀理解題，整題（文章 + 題目 + 選項）放在同一個 chunk。
4. 保持題目原始順序。
5. 一定要標註文法, 並且越詳細越好，有涉及到的文法全部放進來，絕對不可以是 empty list
6. 讀取到的文字可能是破碎的、順序不對的，請務必把相關的題目、選項歸類在一起，如果無法歸類，則直接拋棄，禁止隨意揣測、變造題目
7. 聽力題目(即沒有題幹，只有選項的題目)，請直接跳過
8. 嚴格區分 chunk 類型，先檢查是不是 cloze 或者 reading，如果是，把整篇文章 + 所有對應題目放在同一個 chunk
9. 請不要生成任何不包含 passage 的 reading_question，否則學生將無法判斷答案
10. 同第 9 點， cloze_question 要必須包含 passage，否則請不要生成
11. 檢查 chunk_text 中的資訊是否足以選出答案，如果不行，請刪除此 chunk
12. 檢查 chunk_text 中的資訊是否足以選出答案，如果不行，請刪除此 chunk
13. 檢查 chunk_text 中的資訊是否足以選出答案，如果不行，請刪除此 chunk

【Chunk 類型】 
- single_question
- cloze_question  # 整題文章 + 所有對應題目
- reading_question  # 整題文章 + 所有對應題目

【每個 chunk 欄位，不可以有任何省略,也不可以任意添加】
- chunk_type
- level：{difficulty_level}
- grammar_points（請根據提供的文法清單判斷）
- chunk_text：完整題幹 + 選項 + 文章（如有）
- filename: {pdf_path}

【輸出規則】
- 嚴格輸出 JSON array
- 每個欄位都必須存在，空值填 null 或空 list
- 不回答題目、不提供解析
- 不輸出說明文字或其他文字

【grammar_points list】
一、名詞與冠詞
- 專有名詞
- 可數名詞與不可數名詞
- 名詞單複數
- 不定冠詞 a / an
- 定冠詞 the
- 所有格（’s / of）
- one / ones
- 不定數量詞（some, any, many, much, a few, a little, a lot of, lots of）

二、代名詞
- 人稱代名詞主格
- 人稱代名詞受格
- 所有代名詞（形容詞性 / 名詞性）
- 人稱代名詞複數
- 反身代名詞
- 不定代名詞
- whose 的用法

三、指示與引介結構
- this / that
- these / those
- there is / there are

四、動詞基本句型
- be 動詞現在式
- be 動詞過去式
- 一般動詞現在簡單式
- 第三人稱單數現在式
- 助動詞 do / does / did
- 祈使句

五、時態
- 現在進行式
- 過去簡單式（規則 / 不規則）
- 過去進行式
- 未來式（will / be going to）
- 現在完成式
- 動詞時態綜合應用

六、助動詞與情態動詞
- can
- have to / has to
- should / could / would
- used to

七、疑問句
- Yes / No 問句
- Wh- 問句
- which 的用法
- 問年紀
- 問時間
- 間接問句
- 附加問句

八、連接詞與從屬結構
- and / but
- because / if
- when / before / after
- while / as
- though
- not only…but also…
- no matter + wh-

九、介系詞與副詞
- 地點介系詞
- 時間介系詞
- 交通工具介系詞
- 介系詞片語當形容詞
- 副詞（方式 / 地點 / 時間 / 頻率）
- 頻率副詞

十、形容詞與比較
- 形容詞用法
- 形容詞比較級
- 形容詞最高級
- 副詞比較

十一、特殊動詞
- 感官動詞
- 連綴動詞
- 授與動詞
- 使役動詞
- spend / cost / take / pay
- stop / remember / forget

十二、非限定動詞
- 動名詞
- 不定詞
- too…to…
- so…that…

十三、分詞與語態
- 現在分詞 / 過去分詞
- 情緒動詞與情緒形容詞
- 被動語態

十四、名詞子句與關係子句
- that + 名詞子句
- 名詞子句（what / whether / if）
- 虛主詞 it
- 關係代名詞

十五、其他
- 感嘆句
- 英文中「也」的用法
- it 用法總整理
- 書信格式

【教材內容如下】
\"\"\" {content} \"\"\"
"""

# --- 主流程 ---
for pdf_file in pdf_files:
    if pdf_file in chunked_pdfs:
        print(f"⏩ 跳過已處理：{pdf_file}")
        continue

    pdf_path = os.path.join(PDF_DIR, pdf_file)
    print(f"\n🚀 開始處理：{pdf_file}")

    pages_text = extract_text_by_page(pdf_path)

    all_responses = []

    if "國中" in pdf_path:
        difficulty_level = "junior_high"
    elif "高中" in pdf_path:
        difficulty_level = "senior_high"
    else:
        difficulty_level = "junior_high"

    for page_num, page_text in enumerate(pages_text, start=1):
        print(
            f"\n=== 處理文件 {pdf_file} 第 {page_num} 頁 難度 {difficulty_level}===\n"
        )
        prompt = generate_prompt(page_text, difficulty_level)
        payload = {"model": "gpt-oss:120b", "prompt": prompt, "stream": True}

        page_response = ""
        with requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            stream=True,
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    token_json = json.loads(line.decode())
                    token_text = token_json.get("response", "")
                    page_response += token_text
                    print(token_text, end="", flush=True)

        all_responses.append(page_response)

    print("\n\n--- 完整 JSON 結果 ---")
    # 將每頁結果合併成一個 JSON array
    combined_json = "[{}]".format(",".join([r.strip("[]") for r in all_responses]))
    print(combined_json)

    with open("output.json", "w", encoding="utf-8") as f:
        f.write(combined_json)

    # ===== Flatten JSON =====
    with open("output.json", "r", encoding="utf-8") as f:
        raw_text = f.read()

    objects_text = extract_json_objects_from_text(raw_text)

    print(f"抽出 {len(objects_text)} 個 {{}}")

    # 嘗試轉成真正的 JSON

    valid_objects = []
    for obj in objects_text:
        try:
            valid_objects.append(json.loads(obj))
        except json.JSONDecodeError:
            pass  # 有壞的就跳過

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            last_chunk = json.load(f)
    else:
        last_chunk = []

    last_chunk.extend(valid_objects)
    # print(type(last_chunk))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(last_chunk, f, ensure_ascii=False, indent=2)

    chunked_pdfs.add(pdf_file)
    with open(CHUNKED_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(chunked_pdfs), f, ensure_ascii=False, indent=2)
