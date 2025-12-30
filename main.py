import requests
import json
import os
from dotenv import load_dotenv

prompt = "test"

API_URL = "https://api-gateway.netdb.csie.ncku.edu.tw/api/generate"

load_dotenv()
API_KEY = os.getenv("API_KEY")

payload = {"model": "gpt-oss:120b", "prompt": prompt, "stream": True}
all_responses = []

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
