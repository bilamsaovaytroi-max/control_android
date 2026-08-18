from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

UPSTREAM_URL = "https://github.com/Rtiming/android-adb-automation-kit.git"
UPSTREAM_SHA = "7ed0059e6433269da4f031c25d9bb7a2c7c42289"


@dataclass
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    duration_s: float = 0.0

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def run(
    argv: Iterable[str],
    *,
    cwd: Path,
    timeout: int,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    cmd = [str(x) for x in argv]
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=env,
            shell=False,
        )
        return CommandResult(
            argv=cmd,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            duration_s=time.monotonic() - start,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return CommandResult(
            argv=cmd,
            returncode=124,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
            duration_s=time.monotonic() - start,
        )


def executable_argv(executable: str, args: list[str]) -> list[str]:
    """Build argv safely for native executables and Windows .cmd/.bat shims."""
    if os.name == "nt" and Path(executable).suffix.lower() in {".cmd", ".bat"}:
        comspec = os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe")
        return [comspec, "/d", "/s", "/c", executable, *args]
    return [executable, *args]


def find_executable(name: str, fallbacks: list[str]) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for item in fallbacks:
        if Path(item).exists():
            return item
    return None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def append_log(path: Path, title: str, result: CommandResult) -> None:
    safe_cmd = " ".join(result.argv)
    block = (
        f"\n## {title}\n"
        f"COMMAND: `{safe_cmd}`\n"
        f"EXIT: {result.returncode}\n"
        f"TIMEOUT: {str(result.timed_out).lower()}\n"
        f"DURATION_S: {result.duration_s:.2f}\n\n"
        f"### stdout\n```text\n{result.stdout}\n```\n\n"
        f"### stderr\n```text\n{result.stderr}\n```\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(block)


def sync_upstream(repo_root: Path, log_path: Path) -> Path:
    git = find_executable("git", [])
    if not git:
        raise RuntimeError("git executable not found")

    target = repo_root / "vendor" / "android-adb-automation-kit"
    target.parent.mkdir(parents=True, exist_ok=True)

    if not (target / ".git").exists():
        result = run([git, "clone", "--no-tags", UPSTREAM_URL, str(target)], cwd=repo_root, timeout=180)
        append_log(log_path, "upstream clone", result)
        if not result.ok:
            raise RuntimeError("Unable to clone android-adb-automation-kit")
    else:
        result = run([git, "-C", str(target), "fetch", "origin", "main", "--prune"], cwd=repo_root, timeout=120)
        append_log(log_path, "upstream fetch", result)
        if not result.ok:
            raise RuntimeError("Unable to refresh android-adb-automation-kit")

    result = run([git, "-C", str(target), "checkout", "--detach", UPSTREAM_SHA], cwd=repo_root, timeout=60)
    append_log(log_path, "upstream checkout", result)
    if not result.ok:
        raise RuntimeError(f"Unable to checkout pinned upstream SHA {UPSTREAM_SHA}")

    result = run([git, "-C", str(target), "reset", "--hard", UPSTREAM_SHA], cwd=repo_root, timeout=60)
    append_log(log_path, "upstream reset", result)
    if not result.ok:
        raise RuntimeError("Unable to reset upstream checkout")

    return target


def invoke_codex(
    codex: str,
    repo_root: Path,
    prompt: str,
    output_file: Path,
    log_path: Path,
    title: str,
    timeout: int,
) -> CommandResult:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    argv = executable_argv(codex, [
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C",
        str(repo_root),
        "-s",
        "workspace-write",
        "--output-last-message",
        str(output_file),
    ])
    # Codex exec accepts the prompt via stdin. This avoids Windows cmd.exe
    # command-line length limits for plans, diffs, and failure packets.
    result = run(argv, cwd=repo_root, timeout=timeout, input_text=prompt)
    append_log(log_path, title, result)
    return result


def invoke_claude_review(
    claude: str | None,
    repo_root: Path,
    review_prompt: str,
    output_file: Path,
    log_path: Path,
    title: str,
    timeout: int,
) -> CommandResult:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if not claude:
        result = CommandResult(
            argv=["claude"],
            returncode=127,
            stdout="",
            stderr="Claude CLI not found in PATH or configured fallback path.",
        )
        write_text(output_file, "CLAUDE_REVIEW: UNAVAILABLE\n\nClaude CLI not found.\n")
        append_log(log_path, title, result)
        return result

    argv = executable_argv(claude, [
        "-p",
        "--permission-mode",
        "plan",
        "--output-format",
        "text",
        "--max-turns",
        "4",
        "Review the piped project context. Follow the review contract in that context exactly.",
    ])
    result = run(argv, cwd=repo_root, timeout=timeout, input_text=review_prompt)
    if result.timed_out:
        text = "CLAUDE_REVIEW: TIMEOUT\n\nClaude review exceeded the finite timeout; PM must continue without blocking.\n"
    elif result.ok:
        text = result.stdout.strip() or "CLAUDE_REVIEW: EMPTY\n"
    else:
        text = (
            "CLAUDE_REVIEW: ERROR\n\n"
            f"Exit code: {result.returncode}\n\n"
            f"stderr:\n{result.stderr}\n\nstdout:\n{result.stdout}\n"
        )
    write_text(output_file, text + ("\n" if not text.endswith("\n") else ""))
    append_log(log_path, title, result)
    return result


def parse_pm_result(text: str) -> str | None:
    match = re.search(r"(?im)^PM_RESULT:\s*(PASS|FIX|BLOCKED)\s*$", text)
    return match.group(1).upper() if match else None


def git_diff(repo_root: Path) -> str:
    git = find_executable("git", [])
    if not git:
        return "git unavailable"
    result = run([git, "diff", "--", ".", ":(exclude)vendor/android-adb-automation-kit"], cwd=repo_root, timeout=60)
    return (result.stdout + "\n" + result.stderr).strip()


def hard_test_gate(repo_root: Path, python_cmd: str | None, adb_cmd: str | None, log_path: Path) -> tuple[bool, list[str]]:
    failures: list[str] = []

    if not python_cmd:
        failures.append("Python launcher not found")
    else:
        if Path(python_cmd).name.lower() in {"py.exe", "py"}:
            compile_argv = [python_cmd, "-3.11", "-m", "compileall", "src"]
            pytest_argv = [python_cmd, "-3.11", "-m", "pytest", "-q"]
        else:
            compile_argv = [python_cmd, "-m", "compileall", "src"]
            pytest_argv = [python_cmd, "-m", "pytest", "-q"]

        compile_result = run(compile_argv, cwd=repo_root, timeout=180)
        append_log(log_path, "hard gate: compileall", compile_result)
        if not compile_result.ok:
            failures.append(f"compileall failed ({compile_result.returncode})")

        pytest_result = run(pytest_argv, cwd=repo_root, timeout=300)
        append_log(log_path, "hard gate: pytest", pytest_result)
        if not pytest_result.ok:
            failures.append(f"pytest failed ({pytest_result.returncode})")

    if not adb_cmd:
        failures.append("ADB executable not found")
    else:
        adb_result = run([adb_cmd, "devices"], cwd=repo_root, timeout=30)
        append_log(log_path, "hard gate: adb devices", adb_result)
        if not adb_result.ok:
            failures.append(f"adb devices failed ({adb_result.returncode})")

    return not failures, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex PM -> Claude review -> one Worker -> test/fix loop")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--task-file", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--max-fix-rounds", type=int, default=3)
    parser.add_argument("--claude-timeout", type=int, default=120)
    parser.add_argument("--codex-timeout", type=int, default=900)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    task_file = (repo_root / args.task_file).resolve()
    if not task_file.exists():
        raise SystemExit(f"Task file not found: {task_file}")

    codex = find_executable(
        "codex",
        [r"C:\Users\OS\AppData\Roaming\npm\codex.cmd"],
    )
    if not codex:
        raise SystemExit("Codex CLI not found")

    claude = find_executable(
        "claude",
        [
            r"C:\Users\OS\AppData\Roaming\npm\claude.cmd",
            r"C:\Users\OS\AppData\Local\Programs\claude\claude.exe",
        ],
    )
    python_cmd = find_executable("py", [r"C:\Windows\py.exe"]) or find_executable("python", [])
    adb_cmd = find_executable("adb", [r"C:\Users\OS\AppData\Local\Android\Sdk\platform-tools\adb.exe"])

    runtime = repo_root / ".ai" / "codex" / "runtime" / args.task_id
    reports = repo_root / ".ai" / "codex" / "reports"
    runtime.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    log_path = runtime / "orchestration_log.md"
    write_text(log_path, f"# ORCHESTRATION LOG — {args.task_id}\n")

    pm_contract = read_text(repo_root / ".ai" / "codex" / "PM_PROMPT.md")
    worker_contract = read_text(repo_root / ".ai" / "codex" / "WORKER_CONTRACT.md")
    claude_contract = read_text(repo_root / ".ai" / "codex" / "CLAUDE_REVIEW_PROMPT.md")
    task_text = read_text(task_file)

    upstream_path = sync_upstream(repo_root, log_path)

    plan_file = runtime / "pm_plan.md"
    worker_brief = runtime / "worker_brief.md"
    pm_preplan_last = runtime / "pm_preplan_last.md"
    claude_preplan = runtime / "claude_preplan.md"

    preplan_prompt = f"""{pm_contract}\n\nPHASE: PREPLAN\nTASK_ID: {args.task_id}\nTASK_FILE: {args.task_file}\nUPSTREAM_REFERENCE: {upstream_path}\n\nTASK:\n{task_text}\n\nRequired output actions:\n1. Inspect the current project and upstream reference.\n2. Do NOT edit product source.\n3. Write a bounded implementation plan to {plan_file}.\n4. Write the first worker brief to {worker_brief}.\n5. The worker brief must specify allowed files, exact acceptance criteria, and tests.\n6. End your response with `PM_RESULT: PASS` if the brief is ready, otherwise `PM_RESULT: BLOCKED`.\n"""
    preplan_result = invoke_codex(codex, repo_root, preplan_prompt, pm_preplan_last, log_path, "Codex PM preplan", args.codex_timeout)
    if not preplan_result.ok or not plan_file.exists() or not worker_brief.exists():
        write_text(reports / f"{args.task_id}.md", f"# CODEX PM REPORT — {args.task_id}\n\nRESULT: BLOCKED\nPHASE: PREPLAN\nSee `{log_path.relative_to(repo_root)}`.\n")
        return 2

    claude_prompt = f"""{claude_contract}\n\nREVIEW_KIND: PREPLAN\nTASK_ID: {args.task_id}\n\nTASK:\n{task_text}\n\nPM PLAN:\n{read_text(plan_file)}\n\nWORKER BRIEF:\n{read_text(worker_brief)}\n"""
    invoke_claude_review(claude, repo_root, claude_prompt, claude_preplan, log_path, "Claude preplan review", args.claude_timeout)

    reconcile_last = runtime / "pm_reconcile_last.md"
    reconcile_prompt = f"""{pm_contract}\n\nPHASE: RECONCILE_PREPLAN\nTASK_ID: {args.task_id}\n\nTASK:\n{task_text}\n\nCURRENT PM PLAN:\n{read_text(plan_file)}\n\nCLAUDE REVIEW (advisory; timeout/unavailable must never stall the pipeline):\n{read_text(claude_preplan)}\n\nRequired output actions:\n1. Decide which Claude findings are valid.\n2. Update {plan_file} if needed.\n3. Rewrite {worker_brief} as the final bounded implementation brief.\n4. Do NOT edit product source.\n5. End with `PM_RESULT: PASS` or `PM_RESULT: BLOCKED`.\n"""
    reconcile_result = invoke_codex(codex, repo_root, reconcile_prompt, reconcile_last, log_path, "Codex PM reconcile", args.codex_timeout)
    if not reconcile_result.ok or parse_pm_result(read_text(reconcile_last) if reconcile_last.exists() else "") == "BLOCKED":
        write_text(reports / f"{args.task_id}.md", f"# CODEX PM REPORT — {args.task_id}\n\nRESULT: BLOCKED\nPHASE: RECONCILE_PREPLAN\nSee `{log_path.relative_to(repo_root)}`.\n")
        return 2

    for round_idx in range(args.max_fix_rounds + 1):
        phase_name = "implementation" if round_idx == 0 else f"fix-round-{round_idx}"
        worker_last = runtime / f"worker_{round_idx}_last.md"
        worker_prompt = f"""ROLE=WORKER\n\n{worker_contract}\n\nTASK_ID: {args.task_id}\nROUND: {round_idx}\n\nPM-APPROVED BRIEF:\n{read_text(worker_brief)}\n\nExecute only this brief. Do not plan beyond it. Do not invoke Claude or another Codex. Do not declare DONE.\n"""
        worker_result = invoke_codex(codex, repo_root, worker_prompt, worker_last, log_path, f"Codex Worker {phase_name}", args.codex_timeout)

        pm_review_last = runtime / f"pm_review_{round_idx}.md"
        current_diff = git_diff(repo_root)
        review_prompt = f"""{pm_contract}\n\nPHASE: POST_CODE_REVIEW\nTASK_ID: {args.task_id}\nROUND: {round_idx}\n\nTASK:\n{task_text}\n\nAPPROVED PLAN:\n{read_text(plan_file)}\n\nWORKER BRIEF:\n{read_text(worker_brief)}\n\nWORKER EXIT: {worker_result.returncode}\nWORKER LAST MESSAGE:\n{read_text(worker_last) if worker_last.exists() else '(missing)'}\n\nCURRENT GIT DIFF:\n{current_diff}\n\nRequired actions:\n1. Review the diff strictly against the brief; do not edit product source in this phase.\n2. Run any task-specific non-destructive tests/checks that are necessary and not covered by the hard gate.\n3. End with exactly one token line: `PM_RESULT: PASS`, `PM_RESULT: FIX`, or `PM_RESULT: BLOCKED`.\n4. If FIX, explain the precise failure so the fix brief can be bounded.\n"""
        pm_review_result = invoke_codex(codex, repo_root, review_prompt, pm_review_last, log_path, f"Codex PM post-code review {round_idx}", args.codex_timeout)
        pm_text = read_text(pm_review_last) if pm_review_last.exists() else ""
        pm_status = parse_pm_result(pm_text)

        hard_ok, hard_failures = hard_test_gate(repo_root, python_cmd, adb_cmd, log_path)
        all_ok = worker_result.ok and pm_review_result.ok and pm_status == "PASS" and hard_ok

        if all_ok:
            final_report = (
                f"# CODEX PM REPORT — {args.task_id}\n\n"
                f"RESULT: READY_FOR_USER_TEST\n"
                f"FIX_ROUNDS: {round_idx}\n"
                f"UPSTREAM: `{UPSTREAM_URL}@{UPSTREAM_SHA}`\n"
                f"CLAUDE_PREPLAN: `{claude_preplan.relative_to(repo_root)}`\n"
                f"PM_REVIEW: `{pm_review_last.relative_to(repo_root)}`\n"
                f"LOG: `{log_path.relative_to(repo_root)}`\n\n"
                "All automated gates passed. User should now run the real-device acceptance test defined by the task.\n"
            )
            write_text(reports / f"{args.task_id}.md", final_report)
            print("READY_FOR_USER_TEST")
            return 0

        failure_packet = runtime / f"failure_packet_{round_idx}.md"
        write_text(
            failure_packet,
            f"# FAILURE PACKET — {args.task_id} round {round_idx}\n\n"
            f"WORKER_OK: {worker_result.ok}\n"
            f"PM_STATUS: {pm_status}\n"
            f"PM_EXEC_OK: {pm_review_result.ok}\n"
            f"HARD_GATE_OK: {hard_ok}\n"
            f"HARD_FAILURES: {json.dumps(hard_failures)}\n\n"
            f"## PM review\n{pm_text}\n\n"
            f"## Git diff\n```diff\n{git_diff(repo_root)}\n```\n",
        )

        if pm_status == "BLOCKED":
            write_text(reports / f"{args.task_id}.md", f"# CODEX PM REPORT — {args.task_id}\n\nRESULT: BLOCKED\nPHASE: POST_CODE_REVIEW\nPACKET: `{failure_packet.relative_to(repo_root)}`\n")
            return 3

        if round_idx >= args.max_fix_rounds:
            write_text(reports / f"{args.task_id}.md", f"# CODEX PM REPORT — {args.task_id}\n\nRESULT: FAILED_AFTER_FIX_ROUNDS\nROUNDS: {args.max_fix_rounds}\nPACKET: `{failure_packet.relative_to(repo_root)}`\n")
            return 4

        claude_failure = runtime / f"claude_failure_{round_idx}.md"
        claude_failure_prompt = f"""{claude_contract}\n\nREVIEW_KIND: FAILURE_ANALYSIS\nTASK_ID: {args.task_id}\nROUND: {round_idx}\n\nTASK:\n{task_text}\n\nAPPROVED PLAN:\n{read_text(plan_file)}\n\nFAILURE PACKET:\n{read_text(failure_packet)}\n\nReturn the smallest root-cause analysis and fix recommendation. First line must be `CLAUDE_REVIEW: PASS` if the PM diagnosis is sufficient or `CLAUDE_REVIEW: FIX` if you identify concrete corrections. Do not edit files.\n"""
        invoke_claude_review(claude, repo_root, claude_failure_prompt, claude_failure, log_path, f"Claude failure review {round_idx}", args.claude_timeout)

        fix_plan_last = runtime / f"pm_fix_plan_{round_idx}.md"
        fix_prompt = f"""{pm_contract}\n\nPHASE: FIX_PLAN\nTASK_ID: {args.task_id}\nROUND: {round_idx}\n\nORIGINAL TASK:\n{task_text}\n\nFAILURE PACKET:\n{read_text(failure_packet)}\n\nCLAUDE FAILURE REVIEW (advisory; timeout/unavailable is not blocking):\n{read_text(claude_failure)}\n\nRequired output actions:\n1. Determine the root cause.\n2. Rewrite {worker_brief} as a minimal fix-only brief.\n3. Do NOT edit product source.\n4. Keep exactly one Worker and the original architecture/scope.\n5. End with `PM_RESULT: PASS` when the fix brief is ready, otherwise `PM_RESULT: BLOCKED`.\n"""
        fix_result = invoke_codex(codex, repo_root, fix_prompt, fix_plan_last, log_path, f"Codex PM fix plan {round_idx}", args.codex_timeout)
        fix_text = read_text(fix_plan_last) if fix_plan_last.exists() else ""
        if not fix_result.ok or parse_pm_result(fix_text) != "PASS":
            write_text(reports / f"{args.task_id}.md", f"# CODEX PM REPORT — {args.task_id}\n\nRESULT: BLOCKED\nPHASE: FIX_PLAN\nPACKET: `{failure_packet.relative_to(repo_root)}`\n")
            return 3

    return 5


if __name__ == "__main__":
    sys.exit(main())
