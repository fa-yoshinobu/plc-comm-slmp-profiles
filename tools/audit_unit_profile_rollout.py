#!/usr/bin/env python3
"""Audit the local Ethernet-unit profile rollout without live PLC access."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
PROFILES_REPO = TOOLS_DIR.parent
DEFAULT_SOURCE_ROOT = PROFILES_REPO.parent

UNIT_PROFILES = {
    "melsec:iq-r:rj71en71": "melsec:iq-r",
    "melsec:qcpu:qj71e71-100": "melsec:qcpu",
    "melsec:qnu:qj71e71-100": "melsec:qnu",
    "melsec:qnudv:qj71e71-100": "melsec:qnudv",
    "melsec:lcpu:lj71e71-100": "melsec:lcpu",
}

PINNED_PROFILES_REF = "e7e8f071ff1819a6b088b6a793e6f08029c54e38"

PROFILE_DOCS = {
    "plc-comm-slmp-dotnet": Path("docsrc/user/PROFILES.md"),
    "plc-comm-slmp-python": Path("docsrc/user/PROFILES.md"),
    "plc-comm-slmp-rust": Path("docs/PROFILES.md"),
    "node-red-contrib-plc-comm-slmp": Path("docsrc/user/PROFILES.md"),
    "plc-comm-slmp-cpp-minimal": Path("docsrc/user/PROFILES.md"),
}

FIXTURES = {
    "plc-comm-slmp-dotnet": Path(
        "tests/PlcComm.Slmp.Tests/fixtures/slmp_ethernet_profiles.json"
    ),
    "plc-comm-slmp-python": Path("tests/fixtures/slmp_ethernet_profiles.json"),
    "plc-comm-slmp-rust": Path("tests/fixtures/slmp_ethernet_profiles.json"),
    "node-red-contrib-plc-comm-slmp": Path("test/fixtures/slmp_ethernet_profiles.json"),
    "plc-comm-slmp-cpp-minimal": Path("tests/fixtures/slmp_ethernet_profiles.json"),
}

UPDATE_SCRIPTS = {
    "plc-comm-slmp-dotnet": Path("scripts/update_slmp_profile_jsons.ps1"),
    "plc-comm-slmp-python": Path("scripts/update_slmp_profile_jsons.ps1"),
    "plc-comm-slmp-rust": Path("scripts/update_slmp_profile_jsons.ps1"),
    "node-red-contrib-plc-comm-slmp": Path("scripts/update_slmp_profile_jsons.ps1"),
    "plc-comm-slmp-cpp-minimal": Path("scripts/update_slmp_profile_jsons.ps1"),
}


@dataclass
class Audit:
    checks: int = 0
    failures: list[str] | None = None

    def __post_init__(self) -> None:
        if self.failures is None:
            self.failures = []

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.failures.append(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(read_text(path))


def audit_profile_json(audit: Audit, profiles_repo: Path) -> None:
    data = read_json(profiles_repo / "capability/slmp_ethernet_profiles.json")
    profiles = data["profiles"]
    evidence_files = data.get("evidence_files", {})

    qcpu = profiles.get("melsec:qcpu", {})
    audit.check(qcpu.get("role") == "base", "melsec:qcpu must be role=base")
    audit.check(
        qcpu.get("scope") == "base-profile", "melsec:qcpu must be scope=base-profile"
    )

    for profile_id, base_profile in UNIT_PROFILES.items():
        profile = profiles.get(profile_id)
        audit.check(
            profile is not None, f"{profile_id} must exist in canonical profile JSON"
        )
        if profile is None:
            continue
        audit.check(
            profile.get("base_profile") == base_profile,
            f"{profile_id} must inherit from {base_profile}",
        )
        audit.check(
            profile.get("scope") == "ethernet-unit",
            f"{profile_id} must be scope=ethernet-unit",
        )
        audit.check(profile.get("frame") == "4E", f"{profile_id} must use 4E frame")
        expected_compat = "iQ-R" if profile_id == "melsec:iq-r:rj71en71" else "Q/L"
        audit.check(
            profile.get("compat") == expected_compat,
            f"{profile_id} must use {expected_compat} compatibility",
        )
        audit.check(
            profile.get("role") is None,
            f"{profile_id} must be selectable, not role=base",
        )
        audit.check(
            profile_id in evidence_files, f"evidence_files must include {profile_id}"
        )


def audit_profile_definition_files(audit: Audit, profiles_repo: Path) -> None:
    required = [
        "iq-r_rj71en71_profile_definition.md",
        "qcpu_qj71e71-100_profile_definition.md",
        "qnu_qj71e71-100_profile_definition.md",
        "qnudv_qj71e71-100_profile_definition.md",
        "lcpu_lj71e71-100_profile_definition.md",
    ]
    definitions = profiles_repo / "evidence/profile-definitions"
    for name in required:
        path = definitions / name
        audit.check(path.is_file(), f"missing profile evidence file: {path}")
        if path.is_file():
            text = read_text(path)
            audit.check(
                "|" in text and "Decision" in text,
                f"{name} must include a decision table",
            )


def audit_downstream_fixture(
    audit: Audit, source_root: Path, repo: str, fixture: Path
) -> None:
    path = source_root / repo / fixture
    audit.check(path.is_file(), f"{repo}: missing fixture {fixture}")
    if not path.is_file():
        return
    profiles = read_json(path)["profiles"]
    qcpu = profiles.get("melsec:qcpu", {})
    audit.check(
        qcpu.get("role") == "base", f"{repo}: fixture melsec:qcpu must be role=base"
    )
    audit.check(
        qcpu.get("scope") == "base-profile",
        f"{repo}: fixture melsec:qcpu must be base-profile",
    )
    for profile_id, base_profile in UNIT_PROFILES.items():
        profile = profiles.get(profile_id)
        audit.check(profile is not None, f"{repo}: fixture missing {profile_id}")
        if profile is None:
            continue
        audit.check(
            profile.get("base_profile") == base_profile,
            f"{repo}: {profile_id} fixture base mismatch",
        )
        audit.check(
            profile.get("frame") == "4E", f"{repo}: {profile_id} fixture frame mismatch"
        )
        expected_compat = "iQ-R" if profile_id == "melsec:iq-r:rj71en71" else "Q/L"
        audit.check(
            profile.get("compat") == expected_compat,
            f"{repo}: {profile_id} fixture compat mismatch",
        )


def audit_update_script(
    audit: Audit, source_root: Path, repo: str, script: Path
) -> None:
    path = source_root / repo / script
    audit.check(path.is_file(), f"{repo}: missing update script {script}")
    if path.is_file():
        text = read_text(path)
        audit.check(
            f'$Ref = "{PINNED_PROFILES_REF}"' in text,
            f"{repo}: update script default ref must pin immutable profile commit {PINNED_PROFILES_REF}",
        )


def audit_profile_doc(audit: Audit, source_root: Path, repo: str, doc: Path) -> None:
    path = source_root / repo / doc
    audit.check(path.is_file(), f"{repo}: missing profile doc {doc}")
    if not path.is_file():
        return
    text = read_text(path)
    for profile_id in UNIT_PROFILES:
        audit.check(profile_id in text, f"{repo}: profile doc missing {profile_id}")
    audit.check(
        re.search(r"^\| `melsec:qcpu` \|", text, flags=re.MULTILINE) is None,
        f"{repo}: user profile table must not list melsec:qcpu as selectable",
    )
    audit.check(
        "base-only" in text and "melsec:qcpu:qj71e71-100" in text,
        f"{repo}: doc must explain qcpu successor",
    )


def audit_node_red_options(audit: Audit, source_root: Path) -> None:
    repo = source_root / "node-red-contrib-plc-comm-slmp"
    for name in [
        "nodes/slmp-connection.html",
        "nodes/slmp-read.html",
        "nodes/slmp-write.html",
    ]:
        path = repo / name
        audit.check(path.is_file(), f"node-red: missing {name}")
        if not path.is_file():
            continue
        text = read_text(path)
        audit.check(
            '<option value="melsec:qcpu"' not in text,
            f"node-red: {name} must not expose melsec:qcpu as an option",
        )
    probe = r"""
const runtime = require("./lib/slmp").availablePlcProfiles();
const routes = new Map();
const RED = {
  auth: { needsPermission: () => (_request, _response, next) => next() },
  httpAdmin: { get: (path, ...handlers) => routes.set(path, handlers.at(-1)) },
  nodes: { registerType: () => undefined },
};
require("./nodes/slmp-connection")(RED);
const handler = routes.get("/plc-comm/slmp/profiles");
if (typeof handler !== "function") throw new Error("profile admin endpoint was not registered");
let responsePayload;
handler({}, { json: (payload) => { responsePayload = payload; } });
process.stdout.write(JSON.stringify({
  runtime,
  admin: responsePayload.map((entry) => entry.name),
}));
"""
    try:
        completed = subprocess.run(
            ["node", "-e", probe],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
    ) as exc:
        audit.check(False, f"node-red: dynamic profile API probe failed: {exc}")
        return

    runtime_profiles = payload.get("runtime", [])
    admin_profiles = payload.get("admin", [])
    audit.check(
        admin_profiles == runtime_profiles,
        "node-red: admin profile endpoint must mirror availablePlcProfiles()",
    )
    audit.check(
        "melsec:qcpu" not in runtime_profiles,
        "node-red: base-only melsec:qcpu must not be selectable",
    )
    for profile_id in UNIT_PROFILES:
        audit.check(
            profile_id in runtime_profiles,
            f"node-red: runtime profile API missing {profile_id}",
        )


def audit_docs_site(audit: Audit, source_root: Path) -> None:
    docs = source_root / "plc-comm-docs-site/docs/plc-setup/slmp"
    rj = docs / "rj71en71.md"
    qj = docs / "qj71e71-100.md"
    lj = docs / "lj71e71-100.md"
    audit.check(rj.is_file(), "docs-site: missing RJ71EN71 setup page")
    audit.check(qj.is_file(), "docs-site: missing QJ71E71-100 setup page")
    audit.check(lj.is_file(), "docs-site: missing LJ71E71-100 setup page")
    if rj.is_file():
        text = read_text(rj)
        audit.check(
            "melsec:iq-r:rj71en71" in text, "docs-site RJ page missing unit profile"
        )
        audit.check(
            "4E" in text and "iQ-R" in text,
            "docs-site RJ page must mention 4E and iQ-R",
        )
    if qj.is_file():
        text = read_text(qj)
        for profile_id in [
            "melsec:qcpu:qj71e71-100",
            "melsec:qnu:qj71e71-100",
            "melsec:qnudv:qj71e71-100",
        ]:
            audit.check(profile_id in text, f"docs-site QJ page missing {profile_id}")
        audit.check(
            "4E" in text and "Q/L" in text, "docs-site QJ page must mention 4E and Q/L"
        )
    if lj.is_file():
        text = read_text(lj)
        audit.check(
            "melsec:lcpu:lj71e71-100" in text, "docs-site LJ page missing unit profile"
        )
        audit.check(
            "4E" in text and "Q/L" in text, "docs-site LJ page must mention 4E and Q/L"
        )


def audit_downstream_tools(audit: Audit, profiles_repo: Path) -> None:
    planner = profiles_repo / "tools/run_downstream_read_checks.py"
    audit.check(planner.is_file(), "missing downstream planner tool")
    if planner.is_file():
        planner_text = read_text(planner)
        for profile_id in UNIT_PROFILES:
            audit.check(
                profile_id in planner_text, f"downstream planner missing {profile_id}"
            )
        audit.check(
            "--approved-live-ok" in planner_text,
            "planner must require approved live OK flag",
        )
        audit.check(
            "dry-run only" in planner_text, "planner must default to dry-run messaging"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit non-live unit-profile rollout invariants."
    )
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--profiles-repo", type=Path, default=PROFILES_REPO)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root = args.source_root.resolve()
    profiles_repo = args.profiles_repo.resolve()
    audit = Audit()

    audit_profile_json(audit, profiles_repo)
    audit_profile_definition_files(audit, profiles_repo)
    audit_downstream_tools(audit, profiles_repo)
    for repo, fixture in FIXTURES.items():
        audit_downstream_fixture(audit, source_root, repo, fixture)
    for repo, script in UPDATE_SCRIPTS.items():
        audit_update_script(audit, source_root, repo, script)
    for repo, doc in PROFILE_DOCS.items():
        audit_profile_doc(audit, source_root, repo, doc)
    audit_node_red_options(audit, source_root)
    audit_docs_site(audit, source_root)

    if audit.failures:
        for failure in audit.failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        print(
            f"unit-profile-rollout-audit-failed checks={audit.checks} failures={len(audit.failures)}",
            file=sys.stderr,
        )
        return 1

    print(f"unit-profile-rollout-audit-ok checks={audit.checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
