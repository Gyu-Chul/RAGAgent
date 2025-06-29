import sys
import subprocess

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python js_parse1.py <input_directory> <output_directory>')
        sys.exit(1)

    input_dir, output_dir = sys.argv[1], sys.argv[2]
    cmd = ['node', 'parser.js', input_dir, output_dir]

    try:
        result = subprocess.run(cmd, check=True)
        # Node 출력이 콘솔로 바로 나옴
    except FileNotFoundError:
        print("Error: Node.js가 설치되어 있지 않거나 PATH에 없습니다.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: parser.js 실행 실패 (exit {e.returncode})")
        sys.exit(e.returncode)

    print('JS directory parsing finished.')