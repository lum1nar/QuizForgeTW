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

# ===== 主程式 =====
with open("output.json", "r", encoding="utf-8") as f:
    raw_text = f.read()

objects_text = extract_json_objects_from_text(raw_text)

print(f"抽出 {len(objects_text)} 個 {{}}")

# 嘗試轉成真正的 JSON
import json

valid_objects = []
for obj in objects_text:
    try:
        valid_objects.append(json.loads(obj))
    except json.JSONDecodeError:
        pass  # 有壞的就跳過

with open("all_objects.json", "w", encoding="utf-8") as f:
    json.dump(valid_objects, f, ensure_ascii=False, indent=2)
