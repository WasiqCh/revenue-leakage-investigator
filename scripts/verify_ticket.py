"""Tier-1 verification for a ticket. Runs with no Docker and no network.

    python scripts/verify_ticket.py 014
    python scripts/verify_ticket.py 007 008 015
    python scripts/verify_ticket.py --all
    python scripts/verify_ticket.py --gate 3

What it does
------------
1. Checks every file the ticket names actually exists.
2. Scans the backend for guardrail violations and the correctness traps that
   AI-generated code hits most often (see docs/verification-protocol.md §6).
3. Runs per-ticket checks for the six tickets that are verified individually.
4. Checks process: commit references the ticket, co-author trailer present.

It prints `file:line` for every finding and ends with a verdict:
PASS, FAIL, BLOCKED or NEEDS EVIDENCE. It never marks a ticket PASS when the
work cannot be confirmed without running Docker.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TICKETS = REPO / "docs" / "tickets"
BACKEND = REPO / "backend"
FRONTEND = REPO / "frontend"

SEV1, SEV2, SEV3, SEV4 = "SEV1", "SEV2", "SEV3", "SEV4"
CO_AUTHOR = "Co-authored-by: umer-ch817 <chumerha91@gmail.com>"

# Directories where money correctness is non-negotiable.
MONEY_DIRS = ("backend/app/money", "backend/app/billing", "backend/app/cases")

BANNED_DEPS = ("langchain", "langgraph", "pydantic_ai", "pydantic-ai",
               "llama_index", "llama-index", "crewai", "celery", "redis", "n8n")


class Finding:
    def __init__(self, severity: str, message: str, location: str = ""):
        self.severity, self.message, self.location = severity, message, location

    def __str__(self) -> str:
        loc = f"  [{self.location}]" if self.location else ""
        return f"  {self.severity}  {self.message}{loc}"


# --------------------------------------------------------------------------- parsing

def find_ticket(num: int) -> Path | None:
    matches = sorted(TICKETS.glob(f"TICKET-{num:03d}-*.md"))
    return matches[0] if matches else None


def parse_ticket(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    def field(name: str) -> str:
        m = re.search(rf"^\s*-\s*\*\*{name}:\*\*\s*(.+)$", text, re.M)
        return m.group(1).strip() if m else ""

    deliverables = re.findall(r"^- `([^`]+)`\s*$", text, re.M)
    criteria = re.findall(r"^- \[( |x)\] (.+)$", text, re.M)
    return {
        "num": int(re.match(r"TICKET-(\d{3})", path.name).group(1)),
        "title": text.split("\n", 1)[0].lstrip("# ").strip(),
        "status": field("Status"),
        "phase": field("Phase"),
        "deliverables": deliverables,
        "criteria": criteria,
        "text": text,
    }


# --------------------------------------------------------------------------- checks

def check_deliverables(t: dict) -> list[Finding]:
    out = []
    for d in t["deliverables"]:
        if "*" in d:
            if not list(REPO.glob(d)):
                out.append(Finding(SEV2, f"no files match deliverable glob `{d}`", d))
            continue
        if not (REPO / d).exists():
            out.append(Finding(SEV2, f"deliverable missing: `{d}`", d))
    return out


def check_status(t: dict) -> list[Finding]:
    if t["status"].upper() != "DONE":
        return []
    unchecked = [c for mark, c in t["criteria"] if mark == " "]
    if unchecked:
        return [Finding(SEV3, f"marked DONE but {len(unchecked)} criteria unticked",
                        t["title"])]
    return []


def scan_backend() -> list[Finding]:
    """Guardrail and correctness scans. Returns [] if the backend isn't built yet."""
    if not BACKEND.exists():
        return []
    out: list[Finding] = []
    py_files = [p for p in BACKEND.rglob("*.py") if ".git" not in p.parts]

    for p in py_files:
        rel = p.relative_to(REPO).as_posix()
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue

        in_money = any(rel.startswith(d) for d in MONEY_DIRS)
        is_test = "tests" in rel.split("/")

        for i, line in enumerate(lines, 1):
            loc = f"{rel}:{i}"
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            if in_money and re.search(r"\bfloat\s*\(", line):
                out.append(Finding(SEV1, "float() in money logic — must be Decimal", loc))
            if re.search(r"Decimal\(\s*\d+\.\d+", line):
                out.append(Finding(SEV1, "Decimal built from a float literal — use a string", loc))
            if in_money and re.search(r"\b(datetime\.now|utcnow)\s*\(", line):
                out.append(Finding(SEV2, "wall-clock read in money logic — pass as_of_date", loc))
            if re.search(r"\brandom\.(random|randint|choice|shuffle)\s*\(", line):
                out.append(Finding(SEV2, "unseeded randomness — use Random(seed)", loc))
            if re.search(r"\bos\.(environ|getenv)\b", line) and "config.py" not in rel:
                out.append(Finding(SEV2, "environment read outside config.py", loc))
            if re.search(r"except\s+Exception\s*:\s*(pass|\.\.\.)", line):
                out.append(Finding(SEV2, "swallowed exception hides failures", loc))
            if is_test and re.search(r"\b(requests\.|httpx\.(get|post|Client))", line):
                out.append(Finding(SEV2, "network call in test — must be mocked", loc))

        text = "\n".join(lines)
        if re.search(r"(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+source_", text, re.I):
            out.append(Finding(SEV1, "writes to a source_* table — agent must be read-only", rel))
        if re.search(r"(UPDATE\s+invoice|DELETE\s+FROM\s+invoice|UPDATE\s+contract)", text, re.I):
            out.append(Finding(SEV1, "mutates invoice or contract — forbidden", rel))

    return out


def check_banned_deps() -> list[Finding]:
    cfg = BACKEND / "pyproject.toml"
    if not cfg.exists():
        return []
    text = cfg.read_text(encoding="utf-8").lower()
    return [Finding(SEV1, f"banned dependency `{dep}`", "backend/pyproject.toml")
            for dep in BANNED_DEPS if dep in text]


def check_readonly_role() -> list[Finding]:
    sql = REPO / "scripts" / "init_db.sql"
    if not sql.exists():
        return [Finding(SEV2, "scripts/init_db.sql missing", "scripts/init_db.sql")]
    text = sql.read_text(encoding="utf-8")
    if "rl_readonly" not in text:
        return [Finding(SEV1, "read-only role absent from init_db.sql", "scripts/init_db.sql")]
    return []


def check_money_primitives() -> list[Finding]:
    mod = BACKEND / "app" / "money"
    if not mod.exists():
        return []
    text = "\n".join(p.read_text(encoding="utf-8") for p in mod.rglob("*.py"))
    out = []
    if "Decimal" not in text:
        out.append(Finding(SEV1, "money module does not use Decimal", "backend/app/money/"))
    return out


# Per-ticket checks for the six tickets verified individually.
CRITICAL: dict[int, list] = {
    7:  [check_readonly_role],
    8:  [check_money_primitives],
    15: [lambda: _file_must_not_reference(
            BACKEND / "app" / "billing" / "expected_revenue.py",
            ("invoice",), SEV1,
            "expected revenue must not read invoice tables")],
    22: [lambda: _file_must_contain(BACKEND / "app" / "cases" / "fingerprint.py",
                                    ("case_key",), SEV1, "case fingerprinting")],
    26: [lambda: _file_must_contain(BACKEND / "app" / "cases" / "confidence.py",
                                    ("compute_confidence",), SEV1, "confidence engine")],
    30: [lambda: _file_must_contain(BACKEND / "app" / "ai" / "verifier.py",
                                    ("verifier",), SEV1, "verifier")],
}


def _file_must_contain(path: Path, needles: tuple, sev: str, label: str) -> list[Finding]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    missing = [n for n in needles if n not in text]
    rel = path.relative_to(REPO).as_posix()
    return [Finding(sev, f"{label}: missing `{n}`", rel) for n in missing]


def _file_must_not_reference(path: Path, needles: tuple, sev: str, label: str) -> list[Finding]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(REPO).as_posix()
    return [Finding(sev, f"{label}: references `{n}`", rel)
            for n in needles if re.search(rf"\b{n}", text, re.I)]


def check_process(num: int) -> list[Finding]:
    try:
        log = subprocess.run(["git", "log", "--format=%H%n%s%n%b", "-n", "50"],
                             cwd=REPO, capture_output=True, text=True, timeout=20)
    except (subprocess.SubprocessError, OSError):
        return []
    if log.returncode != 0:
        return []
    tag = f"TICKET-{num:03d}"
    blocks = log.stdout.split("\n\n")
    hit = next((b for b in blocks if tag in b), None)
    if hit is None:
        return []
    if CO_AUTHOR not in hit:
        return [Finding(SEV3, f"{tag} commit missing the co-author trailer", tag)]
    return []


# --------------------------------------------------------------------------- runner

def verify(num: int) -> tuple[str, list[Finding]]:
    path = find_ticket(num)
    if path is None:
        return "FAIL", [Finding(SEV1, f"no ticket file for {num}", "docs/tickets/")]

    t = parse_ticket(path)
    findings: list[Finding] = []
    findings += check_deliverables(t)
    findings += check_status(t)
    findings += scan_backend()
    findings += check_banned_deps()
    findings += check_process(num)
    for fn in CRITICAL.get(num, []):
        findings += fn()

    sev1 = [f for f in findings if f.severity == SEV1]
    is_missing = lambda f: ("deliverable missing" in f.message
                            or "no files match" in f.message)
    missing = [f for f in findings if f.severity == SEV2 and is_missing(f)]
    other_sev2 = [f for f in findings if f.severity == SEV2 and not is_missing(f)]

    # A guardrail violation or a real correctness finding fails regardless of state.
    if sev1:
        return ("FAIL", findings)

    if t["status"].upper() == "DONE":
        return ("FAIL" if (missing or other_sev2) else "PASS", findings)

    # Nothing built yet: not a failure, just not started.
    if not any((REPO / d).exists() for d in t["deliverables"] if "*" not in d):
        return ("NOT STARTED", findings)

    if len(other_sev2) >= 3:
        return ("FAIL", findings)

    # Work exists but behaviour cannot be confirmed without running it.
    return ("BLOCKED", findings)


GATES = {1: 5, 2: 10, 3: 15, 4: 20, 5: 25, 6: 30, 7: 35, 8: 40, 9: 45, 10: 50, 11: 52}


def main() -> int:
    ap = argparse.ArgumentParser(description="Tier-1 ticket verification")
    ap.add_argument("tickets", nargs="*", type=int, help="ticket numbers")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--gate", type=int, help="verify every ticket up to gate N")
    args = ap.parse_args()

    if args.all:
        nums = list(range(1, 53))
    elif args.gate:
        nums = list(range(1, GATES.get(args.gate, 5) + 1))
    elif args.tickets:
        nums = args.tickets
    else:
        ap.print_help()
        return 2

    worst = {"PASS": 0, "NOT STARTED": 1, "NEEDS EVIDENCE": 2, "BLOCKED": 3, "FAIL": 4}
    overall = "PASS"
    exit_code = 0

    for n in nums:
        verdict, findings = verify(n)
        title = find_ticket(n)
        name = title.name if title else f"TICKET-{n:03d}"
        relevant = [f for f in findings if f.severity in (SEV1, SEV2)]
        print(f"\n{'=' * 68}\nTICKET-{n:03d}  {verdict}   ({name})")
        if relevant:
            for f in relevant:
                print(f)
        if verdict == "BLOCKED":
            print("  -- cannot be confirmed without Docker; needs `make verify` evidence")
        if worst[verdict] > worst[overall]:
            overall = verdict
        if verdict == "FAIL":
            exit_code = 1

    print(f"\n{'=' * 68}\nOVERALL: {overall}")
    if overall == "FAIL":
        print("SEV1 or repeated SEV2 found. Fix before continuing.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
