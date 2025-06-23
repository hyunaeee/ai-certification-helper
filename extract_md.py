import json
import glob

# 추출할 파일 패턴
json_files = "parser_output_1_1.json"
output_file = "1_1_md.md"

with open(output_file, "w", encoding="utf-8") as out_f:
    with open(json_files, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception as e:
                print(f"Error loading {json_files}: {e}")

            # 각 항목에서 markdown 추출
            for item in data.get("elements", []):
                md = item.get("content", {}).get("markdown", "")
                if md:
                    out_f.write(md)
                    if not md.endswith("\n"):
                        out_f.write("\n")
