from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import os
import sys
import shutil
import subprocess
import tempfile
import time


@dataclass(frozen=True)
class CodingChallengeTestCase:
    name: str
    stdin: str
    expected_stdout: str


@dataclass(frozen=True)
class CodingChallenge:
    id: str
    title: str
    statement: str
    input_format: str
    output_format: str
    constraints: str
    sample_input: str
    sample_output: str
    templates: Dict[str, str]
    tests: List[CodingChallengeTestCase]
    supported_languages: List[str]


def _normalize_output(value: str) -> str:
    return (value or "").strip().replace("\r\n", "\n")


def get_coding_challenges() -> List[CodingChallenge]:
    # NOTE: MVP ships with one challenge; more can be added.
    statement = (
        "Écris un programme qui vérifie si une chaîne de parenthèses est équilibrée.\n\n"
        "Tu reçois une ligne contenant des caractères parmi: ()[]{}\n"
        "Tu dois afficher 'YES' si la chaîne est équilibrée, sinon 'NO'.\n\n"
        "Règles: chaque parenthèse ouvrante doit être fermée dans le bon ordre."
    )

    templates = {
        'python': (
            "import sys\n\n"
            "s = sys.stdin.readline().strip()\n\n"
            "pairs = {')': '(', ']': '[', '}': '{'}\n"
            "stack = []\n\n"
            "ok = True\n"
            "for ch in s:\n"
            "    if ch in '([{':\n"
            "        stack.append(ch)\n"
            "    elif ch in ')]}':\n"
            "        if not stack or stack[-1] != pairs[ch]:\n"
            "            ok = False\n"
            "            break\n"
            "        stack.pop()\n\n"
            "if ok and not stack:\n"
            "    print('YES')\n"
            "else:\n"
            "    print('NO')\n"
        ),
        'cpp': (
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            "    ios::sync_with_stdio(false);\n"
            "    cin.tie(nullptr);\n\n"
            "    string s;\n"
            "    if(!getline(cin, s)) return 0;\n\n"
            "    unordered_map<char,char> pairs{{')','('},{']','['},{'}','{'}};\n"
            "    vector<char> st;\n"
            "    bool ok = true;\n\n"
            "    for(char ch: s){\n"
            "        if(ch=='('||ch=='['||ch=='{') st.push_back(ch);\n"
            "        else if(ch==')'||ch==']'||ch=='}'){\n"
            "            if(st.empty() || st.back()!=pairs[ch]){ ok=false; break; }\n"
            "            st.pop_back();\n"
            "        }\n"
            "    }\n\n"
            "    cout << ((ok && st.empty()) ? \"YES\" : \"NO\") << \"\\n\";\n"
            "    return 0;\n"
            "}\n"
        ),
        'java': (
            "// Java n'est pas activé dans cet environnement (javac non installé).\n"
        ),
    }

    tests = [
        CodingChallengeTestCase("simple_yes", "()\n", "YES\n"),
        CodingChallengeTestCase("simple_no", "(\n", "NO\n"),
        CodingChallengeTestCase("nested_yes", "([]{})\n", "YES\n"),
        CodingChallengeTestCase("cross_no", "([)]\n", "NO\n"),
        CodingChallengeTestCase("empty_yes", "\n", "YES\n"),
        CodingChallengeTestCase("many_yes", "((([[]]))){}\n", "YES\n"),
        CodingChallengeTestCase("many_no", "((([[]]))){{\n", "NO\n"),
        CodingChallengeTestCase("only_close_no", ")]]\n", "NO\n"),
        CodingChallengeTestCase("mix_chars_yes", "a(b[c]{d}e)\n", "YES\n"),
        CodingChallengeTestCase("mix_chars_no", "a(b[c}e)\n", "NO\n"),
    ]

    challenge = CodingChallenge(
        id="balanced-brackets-v1",
        title="Balanced Brackets",
        statement=statement,
        input_format="Une ligne avec une chaîne s.",
        output_format="Afficher YES si s est équilibrée, sinon NO.",
        constraints="0 <= len(s) <= 200000",
        sample_input="([]{})\n",
        sample_output="YES\n",
        templates=templates,
        tests=tests,
        supported_languages=["python", "cpp"],
    )

    return [challenge]


def _compile_cpp(source_path: Path, out_path: Path) -> Tuple[bool, str]:
    try:
        proc = subprocess.run(
            ["g++", "-O2", "-std=c++17", str(source_path), "-o", str(out_path)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        ok = proc.returncode == 0
        output = (proc.stdout or "") + (proc.stderr or "")
        return ok, output
    except FileNotFoundError:
        return False, "g++ not found. C++ compiler is not installed on the server."


def _run_program(cmd: List[str], stdin: str, cwd: Path) -> Tuple[int, str, str, float]:
    start = time.time()
    proc = subprocess.run(
        cmd,
        input=stdin,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        timeout=2,
        env={
            **os.environ,
            "PYTHONUNBUFFERED": "1",
        },
    )
    elapsed_ms = (time.time() - start) * 1000.0
    return proc.returncode, proc.stdout or "", proc.stderr or "", elapsed_ms


def run_coding_challenge(
    *,
    challenge_id: str,
    language: str,
    code: str,
) -> Dict[str, Any]:
    challenges = {c.id: c for c in get_coding_challenges()}
    challenge = challenges.get(challenge_id)
    if not challenge:
        raise ValueError("Unknown challenge")

    if language not in ("python", "cpp", "java"):
        raise ValueError("Unsupported language")

    if language == "java":
        return {
            "ok": False,
            "error": "Java n'est pas activé sur le serveur (javac non installé).",
            "language": language,
            "challenge_id": challenge_id,
            "passed": 0,
            "total": len(challenge.tests),
            "score": 0,
            "compile_output": "",
            "tests": [],
        }

    if language not in challenge.supported_languages:
        raise ValueError("Language not supported for this challenge")

    tmp_dir = Path(tempfile.mkdtemp(prefix="kash-coding-challenge-"))
    try:
        compile_output = ""
        run_cmd: Optional[List[str]] = None

        if language == "python":
            src = tmp_dir / "main.py"
            src.write_text(code or "", encoding="utf-8")
            run_cmd = [sys.executable, str(src)]

        elif language == "cpp":
            src = tmp_dir / "main.cpp"
            bin_path = tmp_dir / ("main.exe" if os.name == "nt" else "main")
            src.write_text(code or "", encoding="utf-8")
            ok, out = _compile_cpp(src, bin_path)
            compile_output = out
            if not ok:
                return {
                    "ok": False,
                    "error": "Compilation failed",
                    "language": language,
                    "challenge_id": challenge_id,
                    "passed": 0,
                    "total": len(challenge.tests),
                    "score": 0,
                    "compile_output": compile_output,
                    "tests": [],
                }
            run_cmd = [str(bin_path)]

        passed = 0
        test_results: List[Dict[str, Any]] = []

        for t in challenge.tests:
            try:
                rc, stdout, stderr, ms = _run_program(run_cmd, t.stdin, tmp_dir)
                actual = _normalize_output(stdout)
                expected = _normalize_output(t.expected_stdout)
                ok = (rc == 0) and (actual == expected)
                if ok:
                    passed += 1
                test_results.append(
                    {
                        "name": t.name,
                        "passed": ok,
                        "runtime_ms": round(ms, 2),
                        "expected": expected,
                        "actual": actual,
                        "stderr": _normalize_output(stderr),
                    }
                )
            except subprocess.TimeoutExpired:
                test_results.append(
                    {
                        "name": t.name,
                        "passed": False,
                        "runtime_ms": 2000.0,
                        "expected": _normalize_output(t.expected_stdout),
                        "actual": "",
                        "stderr": "Timeout",
                    }
                )

        total = len(challenge.tests)
        score = round((passed / total) * 100.0, 2) if total else 0.0

        return {
            "ok": True,
            "error": None,
            "language": language,
            "challenge_id": challenge_id,
            "passed": passed,
            "total": total,
            "score": score,
            "compile_output": _normalize_output(compile_output),
            "tests": test_results,
        }

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
