"""Command line for dry runs, result tables, and training-export."""

import argparse
import sys
from pathlib import Path

from eval_harness.analyze import write_results
from eval_harness.config import EvalConfig, load_config
from eval_harness.export import export_runs
from eval_harness.logs import read_logs, write_logs
from eval_harness.loop import run_trial
from eval_harness.toy import (
    CONFIG_PATH,
    RESULTS_DIR,
    estimate_tokens,
    make_provider,
    toy_client,
    toy_conditions,
    toy_tasks,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eval")
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--project", required=True)
    shared.add_argument("--results-dir", type=Path)
    shared.add_argument("--config", type=Path)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", parents=[shared])
    run.add_argument("--conditions", required=True)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--yes", action="store_true")
    run.add_argument("--trials", type=int)

    analyze = sub.add_parser("analyze", parents=[shared])
    analyze.add_argument("--out", type=Path)

    export = sub.add_parser("export", parents=[shared])
    export.add_argument("--only-passed", action="store_true")
    export.add_argument("--allow-eval-split", action="store_true")
    export.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.project != "toy":
        print(f"Unknown project {args.project}. Available: toy.", file=sys.stderr)
        return 2
    results_dir = args.results_dir or RESULTS_DIR
    config_path = args.config or CONFIG_PATH
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print(f"Config not found: {config_path}", file=sys.stderr)
        return 2
    if args.command == "run":
        return _run(args, results_dir, config)
    if args.command == "analyze":
        return _analyze(results_dir, args.out)
    return _export(results_dir, args.out, args.only_passed, args.allow_eval_split)


def _run(args: argparse.Namespace, results_dir: Path, config: EvalConfig) -> int:
    if args.trials is not None:
        config.trials = args.trials
    names = [name.strip() for name in args.conditions.split(",") if name.strip()]
    conditions = toy_conditions()
    missing = [name for name in names if name not in conditions]
    if missing:
        print(f"Unknown conditions: {', '.join(missing)}", file=sys.stderr)
        return 2
    n_runs = len(toy_tasks()) * len(names) * config.trials
    if args.dry_run:
        print(f"dry-run: no API calls. {n_runs} scripted trials.")
    else:
        print(estimate_tokens(n_runs))
        if config.model_tier:
            print("model_tier is set. A second model was not run.")
        if not args.yes and input("Type y to continue: ").strip().lower() != "y":
            print("Not run.")
            return 1
    logs = []
    for name in names:
        condition = conditions[name]
        for task in toy_tasks():
            for trial in range(config.trials):
                client = (
                    toy_client(task, condition, trial) if args.dry_run else make_provider(config)
                )
                logs.append(
                    run_trial(
                        task,
                        condition,
                        client,
                        trial=trial,
                        max_tool_calls=config.max_tool_calls,
                    )
                )
    write_logs(results_dir / "runs.jsonl", logs, fresh=True)
    print(f"Wrote {len(logs)} runs to {results_dir / 'runs.jsonl'}")
    return 0


def _analyze(results_dir: Path, out: Path | None) -> int:
    logs = read_logs(results_dir / "runs.jsonl")
    if not logs:
        print("No run logs. Nothing to analyze.", file=sys.stderr)
        return 1
    path = out or (results_dir / "results.md")
    write_results(logs, path)
    print(f"Wrote {path}")
    return 0


def _export(results_dir: Path, out: Path, only_passed: bool, allow_eval_split: bool) -> int:
    notice = export_runs(
        read_logs(results_dir / "runs.jsonl"),
        out,
        only_passed=only_passed,
        allow_eval_split=allow_eval_split,
    )
    if notice:
        print(notice, file=sys.stderr)
    print(f"Wrote {out}")
    return 0
