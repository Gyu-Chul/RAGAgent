import subprocess
import os
import sys


def parse_json2(input_dir: str) -> None:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    REPO_BASE_DIR = os.path.join(PROJECT_ROOT, 'repository')
    PARSED_BASE_DIR = os.path.join(PROJECT_ROOT, 'parsed_repository')


    PARSER_SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'parser.js'))

    if not os.path.exists(PARSER_SCRIPT_PATH):
        print(f"[ERROR] Parser script not found at: {PARSER_SCRIPT_PATH}", file=sys.stderr)
        print("Please ensure 'parser.js' is in the same directory as 'parse_json2.py'.", file=sys.stderr)
        return

    try:
        relative_dir = os.path.relpath(input_dir, REPO_BASE_DIR)
        output_dir = os.path.join(PARSED_BASE_DIR, relative_dir)
        os.makedirs(output_dir, exist_ok=True)

        command = ['node', PARSER_SCRIPT_PATH, input_dir, output_dir]

        print(f"Executing JS parsing for directory: {input_dir}")
        print(f"Command: {' '.join(command)}")

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        print(f"[OK] Successfully parsed JS files in: {input_dir}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"[WARN] Warnings during JS parsing: {result.stderr}")

    except FileNotFoundError:
        print(f"[ERROR] 'node' command not found. Please ensure Node.js is installed and in your PATH.",
              file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] JavaScript parsing failed for directory: {input_dir} → {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {input_dir} → {e}", file=sys.stderr)