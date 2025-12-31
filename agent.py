import time
from utils import llm, load_prompt, search_exam_chunks

def agent_answer(user_query):

    if_rag_prompt = load_prompt(
        "if_rag_prompt",
        user_query=user_query,
    )

    rag_flag = llm(if_rag_prompt)

    # yield f"plan:{plan}"

    if "YES" in rag_flag:
        yield "\n此項任務需要調用 FAISS 數據庫，請稍等.....\n"
        time.sleep(2)
        # 2️⃣ 讓 LLM 自己產生 search query

        yield f"""\n我將先搜索 單選題....\n"""
        time.sleep(2)
        cloze_prompt = load_prompt("search_cloze_prompt", user_query=user_query)
        faiss_query = llm(cloze_prompt, "gpt-oss:20b")

        yield f"""\n我根據你的要求生成了一段語義化的 search query: \n\n{faiss_query}\n"""
        time.sleep(4)

        results, searchstr = search_exam_chunks(faiss_query)
        time.sleep(4)

        yield searchstr

        yield f"""\n現在搜索 閱讀題組....\n"""
        time.sleep(2)
        reading_prompt = load_prompt("search_reading_prompt", user_query=user_query)
        faiss_query = llm(reading_prompt, "gpt-oss:20b")

        yield f"""\n我根據你的要求生成了一段語義化的 search query: \n\n{faiss_query}\n"""
        time.sleep(4)

        results_tmp, searchstr_tmp = search_exam_chunks(faiss_query)
        results.extend(results_tmp)
        searchstr += searchstr_tmp
        time.sleep(4)

        yield searchstr_tmp

        yield f"\n總共爲您找尋了最相關的 {len(results)} 題英文考題\n"
        time.sleep(3)

        # 3️⃣ 把結果丟回給 LLM 用

        yield f"\n即將開始生成 {user_query} 相關的題目，將會耗時 3 - 5 分鐘\n"
        time.sleep(2)

        yield "\n 生成中... \n"

        generate_exam_prompt = load_prompt(
            "generate_exam_prompt", user_query=user_query, results=results
        )
        yield llm(generate_exam_prompt, "gpt-oss:120b")

    else:
        yield "我可以直接回答這個問題:"
        yield llm(user_query)

    return
