import requests
import json
import os
import faiss
import numpy as np
import time
from dotenv import load_dotenv

prompt = "test"

EMBEDDINGMODEL = "embeddinggemma"

searchstr = ""

# open matadata
with open("exam_chunks_meta.json", "r", encoding="utf-8") as f:
    metadatas = json.load(f)

# 1️⃣ 讀取已存的 faiss index
index = faiss.read_index("exam_chunks.faiss")

API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"
# API_URL = "http://localhost:11434/api/generate"
EMBEDDING_URL = "http://localhost:11434/api/embed"
# EMBEDDING_URL = "http://ollama:11434/api/embed"

load_dotenv()
API_KEY = os.getenv("API_KEY")

def embed_text(text, model=EMBEDDINGMODEL):
    resp = requests.post(
        EMBEDDING_URL,
        json={"model": model, "input": text},
    )
    resp.raise_for_status()
    return resp.json()["embeddings"]

def search_exam_chunks(query: str):
    global searchstr
    query_vec = embed_text(query)

    # 確保形狀是 (1, dim)
    if isinstance(query_vec[0], list):
        query_vec = np.array(query_vec, dtype="float32")
    else:
        query_vec = np.array([query_vec], dtype="float32")

    # 4️⃣ 搜索，取前 k 個最相似
    k = 50
    distances, indices = index.search(query_vec, k)

    results = []
    # 5️⃣ 根據 indices 找回 metadata
    for idx, dist in zip(indices[0], distances[0]):
        meta = metadatas[idx]
        results.append(
            {
                "chunk_text": meta["chunk_text"],
                # "grammar_points": meta["grammar_points"],
                # "chunk_type": meta["chunk_type"],
                # "filename": meta["filename"],
            }
        )
        print(
            f"距離: {dist:.4f} | 題目類型: {meta['chunk_type']} | 文法類型: {meta['grammar_points']} 來源: {meta['source']}"
        )
        print(meta["chunk_text"])
        print("=" * 50)

        searchstr += f"\n距離: {dist:.4f} | 題目類型: {meta['chunk_type']} | 文法類型: {meta['grammar_points']} 來源: {meta['source']}\n"
        searchstr += meta["chunk_text"] + "\n"
        searchstr += "=" * 50 + "\n"

    return results

def llm(user_query, llmmodel="gemma3:4b"):
    payload = {"model": llmmodel, "prompt": user_query, "stream": True}

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
    return page_response

def agent_answer(user_query):
    # 1️⃣ 先問 LLM：要不要搜尋？
    # yield f"\n您的要求爲:{user_query}\n"
    # time.sleep(3)

    plan = llm(
        f"""
你是一個英文考題助教 AI。

你可以使用以下工具：
- search_exam_chunks(query, filters)：
  用來搜尋題庫中的考題與文法資料。

工作規則：
1. 如果問題包含“出題”：
   回答 YES

2. 如果只是一般常識或簡單英文
   回答 NO

最後輸出：
只回答 YES 或 NO。

問題：
{user_query}
"""
    )
    # yield f"plan:{plan}"

    if "YES" in plan:
        yield "\n此項任務需要調用 FAISS 數據庫，請稍等.....\n"
        time.sleep(2)
        # 2️⃣ 讓 LLM 自己產生 search query
        search_query = llm(
            f"""
你是一個專門為「英文考題資料庫」設計的檢索查詢生成器。

【任務】
請將下列使用者需求，生成**一個完整的、語義化的單行句子**，作為「適合向量檢索（FAISS）」的搜尋語句。
生成的句子必須：
- 完整呈現題型與文法概念
- 語意清楚、簡潔明確，適合 embedding
- 僅產生一句單行句子
- 不產生解釋、列表、標點符號或多行文字
- 不要回答問題本身

【資料庫特性】
- 資料內容全部都是「臺灣國中／高中英文考題」
- 每筆資料包含文法分類（grammar_points）

【文法清單】
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

【禁止事項】
✘ 不要生成多個查詢  
✘ 不要加引號  
✘ 不要使用問句或寒暄語氣  

【使用者需求】
{user_query}

【範例輸出】
輸入需求: 文法類型: 介系詞
輸出查詢語句: An English multiple-choice question that tests the usage of prepositions such as in, on, at, and to.
""",
            "gpt-oss:20b",
        )

        yield f"""\n我根據你的要求生成了一段語義化的 search query: \n{search_query}\n"""
        time.sleep(4)

        yield f"""\n我將嘗試搜索相關題目....\n"""
        # results = search_exam_chunks(search_query)
        results = search_exam_chunks(search_query)
        time.sleep(4)
        yield searchstr

        yield f"\n總共爲您找尋了最相關的 {len(results)} 題英文考題\n"
        time.sleep(3)

        # 3️⃣ 把結果丟回給 LLM 用

        yield f"\n即將開始生成 {user_query} 相關的題目，將會耗時 3 - 5 分鐘\n"
        time.sleep(2)

        yield "\n 生成中... \n"

        yield llm(
            f"""
你是一位資深的臺灣國中／高中英文出題教師，
熟悉教育部課綱、段考與模擬考的實際出題風格，
並且長期負責正式考卷的命題與審題工作。

你現在的任務是：
【根據提供的考題資料（皆為真實考題），生成「可直接使用於學校段考或模擬考」的新英文試題】。

━━━━━━━━━━━━━━━━━━━━
【重要前提】
━━━━━━━━━━━━━━━━━━━━
1. 提供給你的所有資料皆為「真實考題 chunk」，不是教材、不是文章摘要。
2. 你必須「模仿考題風格」，而不是改寫成教學題或練習題。
3. 出題難度、語氣、選項設計，必須符合臺灣國中／高中正式考試。
4. 題目必須可被單獨作答，禁止生成資訊不足的題目。
5. 務必要有題號，題目的排版參照我給的例句
6. 文法題和 cloze 必須在題幹標示出填空處 _____
7. 三種題型 single_question, cloze, reading_question 缺一不可

━━━━━━━━━━━━━━━━━━━━
【出題任務目標】
━━━━━━━━━━━━━━━━━━━━
請根據檢索到的考題資料，生成「全新但合理變化」的英文試題 總共 20 題 ：

- 題型需與原考題一致（單選、克漏字、閱讀理解）
- 文法重點需與原題相同或高度相關
- 句型、情境、主詞、時間、副詞等可合理變化
- 不可複製原題句子（避免重複題）
- 題目的困難度不可以有太大的變化
- 如果提供的 chunk 資訊不足或者文字內容有誤，允許 LLM 自行做修改
- 必須檢查生成的題目及選項是否合理
- 每個題目及選項的排版風格必須相同

本次的主題爲：{user_query}
出題的方向請以這個爲主

━━━━━━━━━━━━━━━━━━━━
【允許的變化方式（請至少使用其中一種）】
━━━━━━━━━━━━━━━━━━━━
- 更換人名、地名、時間、地點
- 改變句型（主動／被動、肯定／否定）
- 調整語意但保留同一文法核心
- 更換生活情境（校園／家庭／旅遊／購物等）
- 調整選項干擾度（但不可出現語法錯誤）

━━━━━━━━━━━━━━━━━━━━
【禁止事項（非常重要）】
━━━━━━━━━━━━━━━━━━━━
✘ 不可生成教學說明  
✘ 不可附答案或解析  
✘ 不可附上提示
✘ 不可生成無法作答的題目  
✘ 不可生成聽力題  
✘ 不可生成與臺灣考試風格不符的題型（如開放問答）
✘ 不可生成看不懂的題目敘述或是選項

━━━━━━━━━━━━━━━━━━━━
【題型規範】
━━━━━━━━━━━━━━━━━━━━
1. single_question  
- 一題一個題幹  
- 四個選項（A–D）  
- 文法明確、選項設計合理  

2. cloze_question  
- 必須包含完整文章  
- 所有題目都是文章的挖空處要標示出____
- 題目及選項列在文章之後

3. reading_question  
- 必須包含完整 passage  
- 所有題目皆可從文章中判斷答案  
- 不可只生成題目、不附文章  

━━━━━━━━━━━━━━━━━━━━
【語言與格式規範】
━━━━━━━━━━━━━━━━━━━━
- 全部使用正式考試英文
- 選項語法必須正確（除非刻意設計為錯誤選項）
- 題目語氣自然、符合學生年齡
- 不使用過於口語或學術化的英文

━━━━━━━━━━━━━━━━━━━━
【最終輸出要求】
━━━━━━━━━━━━━━━━━━━━
- 僅輸出「題目內容」
- 不要輸出說明、解析、標題
- 不要提及你參考了哪些題目
- 輸出內容必須可直接放入正式考卷

【資料庫內容, 出題參照】
{results}

請開始出題。 
""",
            "gpt-oss:120b",
        )

    else:
        # 4️⃣ 不用 RAG，直接回答
        yield "我可以直接回答這個問題:"
        yield llm(user_query)

    return

# llmanswer = agent_answer()
# # llmanswer = agent_answer("介係詞怎麼用")
# print("任務完成")
# print(llmanswer)
