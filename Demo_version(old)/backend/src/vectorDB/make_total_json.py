# make_total_json.py
import argparse
import json
from pathlib import Path

def iter_json_items(p: Path):
    """파일이 리스트면 원소를, 오브젝트면 그 자체를 yield. 실패하면 None."""
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            for item in data:
                yield item
        else:
            yield data
    except Exception as e:
        yield {"_error": f"failed_to_parse:{p.name}", "_reason": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Merge all JSONs under parsed_repository/<repo>.")
    parser.add_argument("--repo", required=True, help="target repo dir under git-agent/parsed_repository")
    parser.add_argument("--format", choices=["jsonl", "json"], default="jsonl",
                        help="output format (default: jsonl)")
    parser.add_argument("--out", help="output path (default auto)")
    args = parser.parse_args()

    # 프로젝트 루트 기준 경로(스크립트 위치를 기준으로 고정)
    PROJECT_ROOT = Path(__file__).resolve().parents[3]  # /home/ubuntu/git-ai
    TARGET_ROOT = PROJECT_ROOT / "git-agent" / "parsed_repository"
    target_dir = TARGET_ROOT / args.repo

    if not target_dir.exists():
        raise SystemExit(f"❌ Not found: {target_dir}")

    # 출력 경로 결정
    if args.out:
        out_path = Path(args.out).resolve()
    else:
        suffix = ".jsonl" if args.format == "jsonl" else ".json"
        out_path = (target_dir / f"{args.repo}__all{suffix}").resolve()

    json_files = sorted(target_dir.rglob("*.json"))
    if not json_files:
        raise SystemExit(f"❌ No JSON files under: {target_dir}")

    print(f"📂 Scan: {target_dir}")
    print(f"🧾 Files: {len(json_files)}")
    print(f"💾 Out: {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    skipped = 0

    if args.format == "jsonl":
        with out_path.open("w", encoding="utf-8") as out:
            for jp in json_files:
                for item in iter_json_items(jp):
                    if isinstance(item, dict) and "_error" in item:
                        skipped += 1
                        continue
                    # 소스 파일 정보 추가(후속 임베딩/디버깅용)
                    if isinstance(item, dict):
                        item.setdefault("_source_file", str(jp.relative_to(target_dir)))
                    out.write(json.dumps(item, ensure_ascii=False) + "\n")
                    total += 1
    else:
        merged = []
        for jp in json_files:
            for item in iter_json_items(jp):
                if isinstance(item, dict) and "_error" in item:
                    skipped += 1
                    continue
                if isinstance(item, dict):
                    item.setdefault("_source_file", str(jp.relative_to(target_dir)))
                merged.append(item)
                total += 1
        with out_path.open("w", encoding="utf-8") as out:
            json.dump(merged, out, ensure_ascii=False, indent=2)

    print(f"✅ Done. merged items: {total}, skipped: {skipped}")

if __name__ == "__main__":
    main()
