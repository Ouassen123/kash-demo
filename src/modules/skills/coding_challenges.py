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


def _balanced_brackets_challenge() -> CodingChallenge:
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
            "# TODO: vérifie si s est une chaîne de parenthèses équilibrée\n"
            "# Affiche 'YES' si équilibrée, sinon 'NO'\n"
        ),
        'cpp': (
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            "    ios::sync_with_stdio(false);\n"
            "    cin.tie(nullptr);\n\n"
            "    string s;\n"
            "    if(!getline(cin, s)) return 0;\n\n"
            "    // TODO: vérifie si s est équilibrée\n"
            "    // Affiche YES ou NO\n\n"
            "    return 0;\n"
            "}\n"
        ),
        'javascript': (
            "const readline = require('readline');\n"
            "const rl = readline.createInterface({ input: process.stdin });\n"
            "rl.on('line', (s) => {\n"
            "    // TODO: vérifie si s est équilibrée\n"
            "    // Affiche 'YES' ou 'NO'\n"
            "});\n"
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

    return CodingChallenge(
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
        supported_languages=["python", "cpp", "javascript"],
    )


def _fizzbuzz_challenge() -> CodingChallenge:
    statement = (
        "Écris un programme qui affiche FizzBuzz de 1 à N.\n\n"
        "Pour chaque nombre i de 1 à N :\n"
        "  - Si i est divisible par 3 et 5, affiche 'FizzBuzz'\n"
        "  - Si i est divisible par 3, affiche 'Fizz'\n"
        "  - Si i est divisible par 5, affiche 'Buzz'\n"
        "  - Sinon affiche i\n\n"
        "Tu reçois un entier N sur l'entrée standard."
    )

    templates = {
        'python': (
            "import sys\n\n"
            "n = int(sys.stdin.readline().strip())\n\n"
            "# TODO: pour i de 1 à n, affiche FizzBuzz/Fizz/Buzz/i\n"
        ),
        'cpp': (
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            "    int n; cin >> n;\n\n"
            "    // TODO: pour i de 1 à n, affiche FizzBuzz/Fizz/Buzz/i\n\n"
            "    return 0;\n"
            "}\n"
        ),
        'javascript': (
            "const readline = require('readline');\n"
            "const rl = readline.createInterface({ input: process.stdin });\n"
            "rl.on('line', (line) => {\n"
            "    const n = parseInt(line.trim());\n"
            "    // TODO: pour i de 1 à n, affiche FizzBuzz/Fizz/Buzz/i\n"
            "});\n"
        ),
        'java': "// Java n'est pas activé dans cet environnement (javac non installé).\n",
    }

    tests = [
        CodingChallengeTestCase("n5", "5\n", "1\n2\nFizz\n4\nBuzz\n"),
        CodingChallengeTestCase("n15", "15\n", "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n"),
        CodingChallengeTestCase("n1", "1\n", "1\n"),
        CodingChallengeTestCase("n3", "3\n", "1\n2\nFizz\n"),
        CodingChallengeTestCase("n10", "10\n", "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n"),
    ]

    return CodingChallenge(
        id="fizzbuzz-v1",
        title="FizzBuzz",
        statement=statement,
        input_format="Un entier N sur une ligne.",
        output_format="N lignes avec FizzBuzz de 1 à N.",
        constraints="1 <= N <= 1000",
        sample_input="5\n",
        sample_output="1\n2\nFizz\n4\nBuzz\n",
        templates=templates,
        tests=tests,
        supported_languages=["python", "cpp", "javascript"],
    )


def _palindrome_challenge() -> CodingChallenge:
    statement = (
        "Écris un programme qui vérifie si une chaîne est un palindrome.\n\n"
        "Tu reçois une ligne de texte. Ignore les espaces, la casse et la ponctuation.\n"
        "Affiche 'YES' si c'est un palindrome, sinon 'NO'."
    )

    templates = {
        'python': (
            "import sys\n\n"
            "s = sys.stdin.readline().strip()\n\n"
            "# TODO: ignore espaces/casse/ponctuation, vérifie si palindrome\n"
            "# Affiche 'YES' ou 'NO'\n"
        ),
        'cpp': (
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            "    string s; getline(cin, s);\n\n"
            "    // TODO: ignore espaces/casse/ponctuation, vérifie palindrome\n"
            "    // Affiche YES ou NO\n\n"
            "    return 0;\n"
            "}\n"
        ),
        'javascript': (
            "const readline = require('readline');\n"
            "const rl = readline.createInterface({ input: process.stdin });\n"
            "rl.on('line', (s) => {\n"
            "    // TODO: ignore espaces/casse/ponctuation, vérifie palindrome\n"
            "    // Affiche 'YES' ou 'NO'\n"
            "});\n"
        ),
        'java': "// Java n'est pas activé dans cet environnement (javac non installé).\n",
    }

    tests = [
        CodingChallengeTestCase("simple_yes", "radar\n", "YES\n"),
        CodingChallengeTestCase("simple_no", "hello\n", "NO\n"),
        CodingChallengeTestCase("phrase_yes", "A man a plan a canal Panama\n", "YES\n"),
        CodingChallengeTestCase("phrase_no", "not a palindrome\n", "NO\n"),
        CodingChallengeTestCase("empty_yes", "\n", "YES\n"),
        CodingChallengeTestCase("numbers_yes", "12321\n", "YES\n"),
        CodingChallengeTestCase("mixed_yes", "Race car\n", "YES\n"),
        CodingChallengeTestCase("single_yes", "a\n", "YES\n"),
    ]

    return CodingChallenge(
        id="palindrome-v1",
        title="Palindrome Check",
        statement=statement,
        input_format="Une ligne de texte.",
        output_format="Afficher YES si c'est un palindrome, sinon NO.",
        constraints="0 <= len(s) <= 100000",
        sample_input="radar\n",
        sample_output="YES\n",
        templates=templates,
        tests=tests,
        supported_languages=["python", "cpp", "javascript"],
    )


def _two_sum_challenge() -> CodingChallenge:
    statement = (
        "Écris un programme qui trouve deux indices dont la somme vaut une cible.\n\n"
        "Tu reçois :\n"
        "  - Ligne 1 : un tableau d'entiers séparés par des espaces\n"
        "  - Ligne 2 : un entier target\n\n"
        "Affiche les deux indices (séparés par un espace) dont la somme vaut target.\n"
        "Il existe toujours exactement une solution."
    )

    templates = {
        'python': (
            "import sys\n\n"
            "nums = list(map(int, sys.stdin.readline().split()))\n"
            "target = int(sys.stdin.readline().strip())\n\n"
            "# TODO: trouve deux indices i, j tels que nums[i] + nums[j] == target\n"
            "# Affiche les deux indices séparés par un espace\n"
        ),
        'cpp': (
            "#include <bits/stdc++.h>\n"
            "using namespace std;\n\n"
            "int main() {\n"
            "    string line; getline(cin, line);\n"
            "    istringstream iss(line);\n"
            "    vector<int> nums; int x;\n"
            "    while (iss >> x) nums.push_back(x);\n"
            "    int target; cin >> target;\n\n"
            "    // TODO: trouve deux indices dont la somme vaut target\n"
            "    // Affiche les indices séparés par un espace\n\n"
            "    return 0;\n"
            "}\n"
        ),
        'javascript': (
            "const readline = require('readline');\n"
            "const rl = readline.createInterface({ input: process.stdin });\n"
            "let lines = [];\n"
            "rl.on('line', (line) => lines.push(line));\n"
            "rl.on('close', () => {\n"
            "    const nums = lines[0].split(' ').map(Number);\n"
            "    const target = parseInt(lines[1]);\n"
            "    // TODO: trouve deux indices dont la somme vaut target\n"
            "    // Affiche les indices séparés par un espace\n"
            "});\n"
        ),
        'java': "// Java n'est pas activé dans cet environnement (javac non installé).\n",
    }

    tests = [
        CodingChallengeTestCase("basic", "2 7 11 15\n9\n", "0 1\n"),
        CodingChallengeTestCase("first_two", "3 2 4\n6\n", "1 2\n"),
        CodingChallengeTestCase("same_value", "3 3\n6\n", "0 1\n"),
        CodingChallengeTestCase("large", "1 5 8 12 3 7\n15\n", "2 3\n"),
        CodingChallengeTestCase("reverse", "10 20 30 40\n70\n", "2 3\n"),
        CodingChallengeTestCase("first_last", "1 2 3 4 5 6\n7\n", "0 5\n"),
    ]

    return CodingChallenge(
        id="two-sum-v1",
        title="Two Sum",
        statement=statement,
        input_format="Ligne 1: tableau d'entiers. Ligne 2: entier target.",
        output_format="Deux indices séparés par un espace.",
        constraints="2 <= len(nums) <= 10000",
        sample_input="2 7 11 15\n9\n",
        sample_output="0 1\n",
        templates=templates,
        tests=tests,
        supported_languages=["python", "cpp", "javascript"],
    )


def get_coding_challenges() -> List[CodingChallenge]:
    return [
        _balanced_brackets_challenge(),
        _fizzbuzz_challenge(),
        _palindrome_challenge(),
        _two_sum_challenge(),
    ]


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

    if language not in ("python", "cpp", "java", "javascript"):
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

        elif language == "javascript":
            src = tmp_dir / "main.js"
            src.write_text(code or "", encoding="utf-8")
            run_cmd = ["node", str(src)]

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
