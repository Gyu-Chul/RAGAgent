import subprocess
import os

def git_clone(repo_url: str, subfolder: str = ".") -> str:
    """
    주어진 repo_url의 Git 레포지토리를 destination 디렉토리로 클론합니다.
    기본 destination은 현재 작업 디렉토리('.')입니다.

    Args:
        repo_url (str): 클론할 Git 레포지토리 주소
        destination (str): 레포지토리를 받을 디렉토리 (기본: 현재 디렉토리)

    Returns:
        str: 성공 시 "SUCCESS", 실패 시 "FAILURE"
    """

    base_dir = "repository"
    # 최종 목적지 경로 결정
    if subfolder:
        dest = os.path.join(base_dir, subfolder)
    else:
        dest = base_dir

    # 디렉토리 유효성 체크
    if os.path.exists(dest) and os.listdir(dest):
        print(f"[ERROR]: '{dest}' 디렉토리가 존재하며 비어 있지 않습니다.")
        return "FAILURE"
    os.makedirs(dest, exist_ok=True)

    try:
        # destination 디렉토리가 없으면 생성
        os.makedirs(dest, exist_ok=True)

        # git clone 실행
        subprocess.run(
            ["git", "clone", repo_url, dest],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("[SUCCESS] 클론 완료:", repo_url, "→", dest)
        return "SUCCESS"
    except subprocess.CalledProcessError as e:
        print("[ERROR] 클론 실패:")
        print("STDERR:", e.stderr)
        return "FAILURE"
