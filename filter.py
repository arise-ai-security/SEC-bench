import argparse, json, os, sys

def collect_names(data, key=None):
    names = []

    def add(s):
        if s is None:
            return
        s = str(s).strip()
        if s:
            names.append(s)

    if isinstance(data, list):
        for item in data:
            if isinstance(item, str) and key is None:
                add(item)
            elif isinstance(item, dict):
                keys = [key] if key else ["name", "filename", "file"]
                for k in keys:
                    if k in item:
                        add(item[k])
                        break
    elif isinstance(data, dict):
        array_keys = [key] if key else ["repos", "files", "items", "data", "entries"]
        for k in array_keys:
            if k in data and isinstance(data[k], list):
                names.extend(collect_names(data[k], key))
                break

    # Deduplicate, keep order
    seen = set()
    result = []
    for n in names:
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result

def endings_from_names(names):
    # Take substring after the last dot; if no dot, use the whole name
    endings = []
    seen = set()
    for n in names:
        end = n.rsplit(".", 1)[-1]
        if end not in seen:
            seen.add(end)
            endings.append(end)
    return endings

def main():
    p = argparse.ArgumentParser(description="Keep files in artifact/input whose base name equals the ending of entries in repos.json.")
    p.add_argument("--input-dir", default="artifact/input")
    p.add_argument("--repos-json", default="repos.json")
    p.add_argument("--json-key", default=None, help="Key in JSON objects holding the names (e.g. name or filename). Optional.")
    p.add_argument("--delete-non-matching", action="store_true", help="Actually delete non-matching files. Default is dry-run.")
    p.add_argument("--case-sensitive", action="store_true", help="Make matching case-sensitive.")
    args = p.parse_args()

    # Load JSON
    try:
        with open(args.repos_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to read {args.repos_json}: {e}", file=sys.stderr)
        sys.exit(1)

    names = collect_names(data, args.json_key)
    if not names:
        print("No names found in repos.json (check structure or --json-key).", file=sys.stderr)
        sys.exit(2)

    # Compute endings (after last '.') and build a lookup set
    endings = endings_from_names(names)
    if not endings:
        print("No endings could be derived from repos.json entries.", file=sys.stderr)
        sys.exit(2)

    if args.case_sensitive:
        allowed = set(endings)
    else:
        allowed = set(e.lower() for e in endings)

    # Scan input dir
    if not os.path.isdir(args.input_dir):
        print(f"Input dir not found: {args.input_dir}", file=sys.stderr)
        sys.exit(3)

    kept, removed = [], []
    for entry in os.scandir(args.input_dir):
        if not entry.is_file():
            continue
        base, ext = os.path.splitext(entry.name)
        key = base if args.case_sensitive else base.lower()
        if key in allowed:
            kept.append(entry.path)
        else:
            removed.append(entry.path)

    # Act
    if args.delete_non_matching:
        for pth in removed:
            try:
                os.remove(pth)
            except Exception as e:
                print(f"Failed to delete {pth}: {e}", file=sys.stderr)

    # Report
    print(f"Matched {len(kept)} file(s). {'Deleted' if args.delete_non_matching else 'Would delete'} {len(removed)} non-matching file(s).")
    for pth in kept:
        print(f"KEEP: {pth}")
    for pth in removed:
        print(("DELETED: " if args.delete_non_matching else "REMOVE: ") + pth)

if __name__ == "__main__":
    main()