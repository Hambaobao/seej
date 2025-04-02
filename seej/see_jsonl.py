import argparse
import json
import os
from pathlib import Path

from seej.tools import get_terminal_width, load_jsonl_iter

try:
    import readchar
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print(f"Please install: `pip install rich readchar`")
    exit(1)

console = Console()


def session_process_norich(v, **kwargs):
    for turn_idx, info in enumerate(v):
        print(f"<{turn_idx}:query>")
        print(info["query"])
        print(f"<{turn_idx}:response>")
        print(info["response"])


def messages_process_norich(v, **kwargs):
    for turn_idx, info in enumerate(v):
        print(f"<{turn_idx}:{info['role']}>")
        print(info["content"])


def session_process(v, md, no_rich, **kwargs):
    if no_rich:
        return session_process_norich(v)

    table = Table(show_header=False)
    table.add_column()
    if md:
        table.add_column(max_width=120)
    else:
        table.add_column()

    Wrapper = lambda v: Markdown(v, code_theme="github", justify="left") if md else Text(v, overflow="fold")

    for turn_idx, info in enumerate(v):
        table.add_row(f"<{turn_idx}:query>", Wrapper(info["query"]), end_section=True)
        table.add_row(f"<{turn_idx}:response>", Wrapper(info["response"]), end_section=True)

    console.print(table, crop=False, justify="left")


def messages_process(v, md, no_rich, **kwargs):
    if no_rich:
        return messages_process_norich(v)

    table = Table(show_header=False)
    table.add_column()
    if md:
        table.add_column(max_width=120)
    else:
        table.add_column()

    Wrapper = lambda v: Markdown(v, code_theme="github", justify="left") if md else Text(v, overflow="fold")

    for turn_idx, info in enumerate(v):
        table.add_row(f"<{turn_idx}:{info['role']}>", Wrapper(info["content"]), end_section=True)

    console.print(table, crop=False, justify="left")


def renderable_norich(v):
    print(v)


def renderable(v, md, no_rich, **kwargs):
    if no_rich:
        return renderable_norich(v)

    if isinstance(v, dict):
        for sub_k, sub_v in v.items():
            print(f"< Key = {sub_k} >")
            mapper.get(sub_k, eye)(sub_v, **kwargs)
            print()
    elif isinstance(v, list):
        for sub_v in v:
            eye(sub_v)
            print()
    else:
        Wrapper = lambda v: Markdown(v, code_theme="github", justify="left") if md else Text(v, overflow="fold", no_wrap=True)
        console.print(Wrapper(v))


def eye(v, **kwargs):
    print(v)


def show_one_test(v, **kwargs):
    try:
        if not len(v):
            return eye(v)

        ex = min(v, key=lambda e: len(json.dumps(v)))
        input_s = ex["input"]
        output_s = ex["output"]
        testtype = ex["testtype"]
        print(f"(Total Sample={len(v)})")
        print(f"<Sampled Input:{testtype}>")
        print(input_s)
        print(f"<Sampled Output>")
        print(output_s)
    except KeyboardInterrupt as e:
        print(f"Skip Loading")


def show_one_submission(v, **kwargs):
    # v = list(filter(lambda e: "author" in e, v))
    if not len(v):
        print(f"Empty: {len(v)=}")
        return

    ex = min(v[-10:], key=lambda e: len(json.dumps(v)))
    print(f"(Total Submissions={len(v)})")
    for k, v in ex.items():
        print(f"<Sampled Submission - {k}>")
        mapper.get(k, eye)(v, **kwargs)
        # print("\t" + "-" * 50)


def show_one_gen(v, **kwargs):
    if isinstance(v, list):
        return renderable(v[0], **kwargs)
    else:
        return renderable(v, **kwargs)


def show_bug_codes(vs, **kwargs):
    for idx, bug_code in enumerate(vs):
        print(f"<Bug Code - {idx}>")
        for k, v in bug_code.items():
            print(f"<Key = {k}>")
            print(v)


mapper = {
    "session": session_process,
    "messages": messages_process,
    "text": renderable,
    "vllm_generated": renderable,
    "parsed_ret": renderable,
    "public_test_cases": show_one_test,
    "private_test_cases": show_one_test,
    "generated_test_cases": show_one_test,
    "submissions": show_one_submission,
    "failed_submissions": show_one_submission,
    "gen": show_one_gen,
    "bug_codes": show_bug_codes,
    "parsed_4o": renderable,
}


def control_str(s, wrap=False):
    content = Text(s, style="bold red", overflow="fold")
    if wrap:
        content = Panel(content, expand=False, title="Control")

    console.print(content)


class ExampleNavigator:

    def __init__(self, file_path, start_idx=0, md=False, no_rich=False, cond_fn_str=None):
        self.file_path = file_path
        self.start_idx = start_idx
        self.md = md
        self.no_rich = no_rich
        self.cond_fn_str = cond_fn_str
        if self.cond_fn_str is not None:
            self.cond_fn = eval(cond_fn_str)
        else:
            self.cond_fn = None

        self.current_idx = -1
        self.iterator = load_jsonl_iter(file_path, skip=start_idx)
        self.example_history = []

        self.navigate_next()
        self.run()

    def run(self):
        while True:
            try:
                key = readchar.readkey()
                if key == readchar.key.UP or key == readchar.key.LEFT:
                    self.navigate_previous()
                elif key == readchar.key.DOWN or key == readchar.key.RIGHT or key == readchar.key.ENTER:
                    self.navigate_next()
                elif key.casefold() in ["q", "x"]:
                    control_str("Quit.")
                    break
                elif key.casefold() == "t":
                    self.toggle_render_mode()
            except KeyboardInterrupt:
                control_str("Quit.")
                break
            except Exception as e:
                raise e

    def toggle_render_mode(self):
        self.no_rich = not self.no_rich
        self.display_current_example()
        control_str(f"Rendering mode toggled to {'raw' if self.no_rich else 'rich'}.")

    def navigate_previous(self):
        if self.current_idx > 0:
            self.current_idx -= 1
            self.display_current_example()
        else:
            control_str("Cannot go back further.")

    def try_get_next(self):
        while True:
            try:
                new_one = next(self.iterator)
                return new_one
            except:
                print(new_one)
                print(f"Bad: `try_get_next`")
                continue

    def navigate_next(self):
        if self.current_idx < len(self.example_history) - 1:
            self.current_idx += 1
        else:
            try:
                if self.cond_fn is None:
                    new_example = next(self.iterator)
                    # new_example = self.try_get_next()
                else:
                    while True:
                        new_example = next(self.iterator)
                        # new_example = self.try_get_next()
                        try:
                            if self.cond_fn(new_example):
                                # print(f"ON: {new_example['source'] = }, {self.current_idx=}")
                                # print(f"MATCHED")
                                break
                        except:
                            # print(f"Failed")
                            continue
                        # input(">>>")

                self.current_idx += 1
                self.example_history.append((self.current_idx + self.start_idx, new_example))
            except StopIteration:
                control_str("End of examples.")
                exit(0)

        self.display_current_example()

    def display_current_example(self):
        os.system("clear")
        file_idx, ex = self.example_history[self.current_idx]
        largest_idx, _ = self.example_history[-1]

        for k, v in ex.items():
            print(f"[{k}]")
            mapper.get(k, eye)(v, md=self.md, no_rich=self.no_rich)
            print("-" * get_terminal_width())

        s = f"IDX={file_idx} | LOADED=[{self.start_idx}, {largest_idx}]\n\n"
        s += "Prev(LEFT)  Next(RIGHT)  (Q)uit  (T)oggle"
        control_str(s, wrap=False)
        control_str(f"\nCond: `{self.cond_fn_str}`", wrap=False)


def build_conditions(file, cond_str_list, hint_keys):
    if not cond_str_list:
        return None

    with Path(file).open("r") as f:
        first_line = json.loads(f.readline().strip())

    all_prepared_keys = list(first_line.keys())
    if hint_keys is not None:
        all_prepared_keys += list(hint_keys)
    all_keys = sorted(set(all_prepared_keys), key=len)[::-1]
    print(all_keys)

    cond_fn_strs = []
    for cond_str in cond_str_list:
        matched_keys = []
        remains = cond_str[::]
        for el_key in all_keys:
            if el_key in remains:
                matched_keys.append(el_key)
                remains = remains.replace(el_key, ":>-<:")
                # print(f"Matched: {el_key} -> {remains}")

        this_branch = cond_str
        for matched_key in matched_keys:
            this_branch = this_branch.replace(matched_key, f"ex['{matched_key}']")
        print(f"Cond `{cond_str}` hits: {matched_keys} -> {this_branch}")
        cond_fn_strs.append(f"( {this_branch} )")

    cond_fn_str = "lambda ex: " + " and ".join(cond_fn_strs)

    print("=" * 120)
    print(f"Assembled: ")
    print(cond_fn_str)
    print("=" * 120)

    return cond_fn_str


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    parser.add_argument("-I", "--idx", type=int, default=0, help="Start from the given index.")
    parser.add_argument("-R", "--raw", action="store_true", default=False, help="Instead of using rich.Text to render, output raw string.")
    parser.add_argument("-M", "--md", action="store_true", default=False, help="Enable markdown renderer, no effect when `-R` / `--raw`.")
    parser.add_argument("-C", "--cond", type=str, nargs="+", help="List of boolean exprs to filter.")
    parser.add_argument("-K", "--hint-keys", type=str, nargs="+", help="List of keys available that may not in the first example.")
    args = parser.parse_args()

    if not Path(args.file).exists():
        raise ValueError(f"{args.file} doesn't exist.")

    condition_fn_str = build_conditions(args.file, args.cond, args.hint_keys)

    navigator = ExampleNavigator(args.file, start_idx=args.idx, md=args.md, no_rich=args.raw, cond_fn_str=condition_fn_str)


if __name__ == "__main__":
    main()
