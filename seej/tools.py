import json
import shutil
import time
from math import ceil
from pathlib import Path

from tqdm import tqdm


def get_terminal_width():
    try:
        return shutil.get_terminal_size().columns
    except:
        return 120


def save_list(data_list, file):
    print(f"Saving...")
    with Path(file).open("w") as f:
        for ex in tqdm(data_list, leave=False):
            json.dump(ex, f, indent=None, ensure_ascii=False)
            f.write("\n")
    print(f"Saved => {file}")


def confirm_continue():
    while True:
        response = input("Confirm? [Y/n]: ").strip().lower()
        if response in ["y", "yes", ""]:
            return True
        elif response in ["n", "no"]:
            print("Exiting the script.")
            exit(0)
        else:
            print("Invalid input.")


def save_list_limited(data_list, folder, max_ex, suffix="jsonl"):
    total = len(data_list)
    num_parts = ceil(total / max_ex)

    print(f"Saving {total} items to {num_parts} parts.")
    for i in range(num_parts):
        start_idx = i * max_ex
        end_idx = min((i + 1) * max_ex, total)
        part_data = data_list[start_idx:end_idx]

        part_file = folder.joinpath(f"part{i+1:03d}.{suffix}")
        with part_file.open("w") as f:
            for ex in part_data:
                json.dump(ex, f, indent=None, ensure_ascii=False)
                f.write("\n")

        print(f"Saved [{i}] {len(part_data)} => {part_file}")


def generate_random_seed():
    current_time = time.time()
    seed = int(current_time * 1000) % (2**32 - 1)
    return seed


def load_jsonl_iter(file, limit=None, skip=None):
    if skip is None:
        skip = 0

    with Path(file).open("r") as f:
        for idx, line in enumerate(f):
            if idx < skip:
                continue
            if limit and idx >= skip + limit:
                return
            if line.strip():
                yield json.loads(line.strip())
