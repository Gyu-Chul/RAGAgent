import os
import json

root_dir = "converted/git-ai-sample-converted"
exclude_files = {"last_event_state.json", "repo_events.json"}
datas = []

for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".json") and filename not in exclude_files:
            full_path = os.path.join(dirpath, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict) and "file_path" in content:
                        datas.append(content)
                    else:
                        datas.append({
                            "file_path": full_path,
                            "error": "Missing expected keys"
                        })
            except Exception as e:
                # 디코딩/파싱 오류 포함
                datas.append({
                    "file_path": full_path,
                    "error": str(e)
                })

### repo_events,last_event_state json 파싱 로직 추가 필요