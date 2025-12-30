import json

# 設定檔案路徑
INPUT_FILE = "all_objects.json"
OUTPUT_FILE = "all_objects_clean.json"

# 欄位要求
REQUIRED_FIELDS = ["chunk_type", "level", "grammar_points", "chunk_text"]

def is_valid(obj):
    """檢查物件是否符合規範"""
    for field in REQUIRED_FIELDS:
        if field not in obj:
            return False

    return True

# 讀取原始 JSON
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# 過濾符合規範的物件
clean_data = [obj for obj in data if is_valid(obj)]

print(f"原始物件數量: {len(data)}")
print(f"符合規範物件數量: {len(clean_data)}")

# 儲存清理後的 JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(clean_data, f, ensure_ascii=False, indent=2)

print(f"清理完成，已存成 {OUTPUT_FILE}")
