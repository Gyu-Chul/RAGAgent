import subprocess
import os
import sys
import json
from typing import List, Dict, Union


def parse_json3(file_path: str) -> None:
    """
    자바 파일 경로(`file_path`)를 받아, Maven으로 빌드된 Java 파서(.jar)를 실행하여
    결과를 'parsed_repository' 폴더에 .json 파일로 저장합니다.
    """
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    REPO_BASE_DIR = os.path.join(PROJECT_ROOT, 'repository')
    PARSED_BASE_DIR = os.path.join(PROJECT_ROOT, 'parsed_repository')

    PARSER_JAR_PATH = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'target', 'java-parser-1.0.0-jar-with-dependencies.jar'
    ))

    if not os.path.exists(PARSER_JAR_PATH):
        print(f"[ERROR] 파서 JAR 파일을 찾을 수 없습니다: {PARSER_JAR_PATH}", file=sys.stderr)
        print("스크립트를 실행하기 전에 'parse_json3' 디렉터리에서 'mvn package' 명령을 실행하여 프로젝트를 빌드하세요.", file=sys.stderr)
        return

    try:
        relative_path = os.path.relpath(file_path, REPO_BASE_DIR)
        json_output_path = os.path.join(PARSED_BASE_DIR, os.path.splitext(relative_path)[0] + '.json')
        os.makedirs(os.path.dirname(json_output_path), exist_ok=True)

        # ✨ 여기가 수정된 부분입니다.
        # Java Virtual Machine(JVM)이 실행될 때부터 UTF-8 인코딩을 사용하도록 강제하는 옵션을 추가합니다.
        command = ['java', '-Dfile.encoding=UTF-8', '-jar', PARSER_JAR_PATH, file_path]

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            # 이제 양쪽 다 UTF-8을 사용하므로 encoding만 명시하고 errors 옵션은 제거합니다.
            encoding='utf-8'
        )

        if not result.stdout.strip():
            # 빈 결과는 경고 없이 조용히 넘어가는 것이 더 깔끔할 수 있습니다.
            return

        parsed_entries = json.loads(result.stdout)

        if parsed_entries:
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_entries, f, ensure_ascii=False, indent=2)
            # 성공 메시지는 너무 많으므로 주석 처리합니다.
            # print(f"[OK] 생성됨: {json_output_path}")

    except FileNotFoundError:
        print("[ERROR] 'java' 명령을 찾을 수 없습니다. JDK가 설치되어 있고 PATH에 등록되어 있는지 확인하세요.", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Java 파서 실행 실패: {file_path}", file=sys.stderr)
        # Stderr가 있는 경우, 자바 쪽에서 발생한 에러를 출력하여 디버깅을 돕습니다.
        if e.stderr:
            print(f"  [Java Stderr]: {e.stderr}", file=sys.stderr)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Java 파서의 출력(JSON)을 디코딩하는 데 실패했습니다: {file_path}", file=sys.stderr)
        print(f"  [Received Output]: {result.stdout}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] 예기치 않은 오류 발생: {file_path} -> {e}", file=sys.stderr)