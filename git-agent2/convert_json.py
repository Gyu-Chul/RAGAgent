import os
import json

target_repo_path = "target_repositorys/git-ai-sample"
converted_base_path = "converted/git-ai-sample-converted"

def convert_file_to_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return {
            "file_path": file_path.replace("\\", "/"),
            "content": [line.rstrip("\n") for line in lines]  # 줄 단위 리스트
        }
    except Exception:
        # 읽기 불가능한 경우에도 경로는 기록, 내용은 undefined
        return {
            "file_path": file_path.replace("\\", "/"),
            "content": "undefined"
        }

def process_directory(source_dir, target_dir):
    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        converted_dir = os.path.join(target_dir, rel_path)

        os.makedirs(converted_dir, exist_ok=True)

        for file in files:
            original_file_path = os.path.join(root, file)
            json_filename = file + ".json"
            converted_file_path = os.path.join(converted_dir, json_filename)

            file_json = convert_file_to_json(original_file_path)

            with open(converted_file_path, "w", encoding="utf-8") as out_f:
                json.dump(file_json, out_f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    os.makedirs(converted_base_path, exist_ok=True)
    process_directory(target_repo_path, converted_base_path)
    print(f"✅ 변환 완료: {converted_base_path} 경로에 저장됨")
