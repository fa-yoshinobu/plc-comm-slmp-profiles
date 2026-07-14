#!/usr/bin/env python3
"""Plan-driven unit probe sweep.

Removes operator discretion from unit investigations:

- The plan JSON is the only instruction. Every required item in
  tools/unit_probe_plan_required.json must be present in the plan
  (or carry an explicit reviewed "waiver" string), otherwise the run
  is refused before any communication.
- Writes are allowed only to devices in the plan's "write_allow" list,
  with a span large enough for the item's cap. A write item without an
  allowlisted target is a validation error, never a silent skip.
- Limits are measured by automatic boundary search (exponential then
  binary), so fixed guess counts cannot be substituted for evidence.
- Each item records its measured outcome, and the run ends with a completeness summary. Exit codes:
  0 = complete, 2 = plan validation failed, 3 = completed with errors.
- One-off raw probes are discovery only. If they reveal profile-relevant facts,
  add a structured item here and in the reviewed plan instead of archiving an
  ad-hoc probe result.

Usage:
  python tools/run_unit_probe_plan.py --plan <plan.json> [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

TOOLS_DIR = Path(__file__).resolve().parent
REPO = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import live_profile_probe as probe  # noqa: E402

if getattr(sys, "frozen", False):  # bundled single-file executable
    MANIFEST_PATH = Path(getattr(sys, "_MEIPASS")) / "tools" / "unit_probe_plan_required.json"
else:
    MANIFEST_PATH = TOOLS_DIR / "unit_probe_plan_required.json"
RANDOM_FIELD_CAP = 255  # count fields in random/monitor payloads are one byte

# item type -> (param name, span need) for write allowlist validation
WRITE_PARAMS: dict[str, list[tuple[str, str]]] = {
    "write_word_verify": [("device", "one")],
    "write_bit_verify": [("device", "one")],
    "boundary_direct_write_word": [("device", "cap")],
    "boundary_direct_write_bit": [("device", "cap")],
    "boundary_random_write_word": [("word_device", "cap")],
    "boundary_random_write_word_weighted": [("dword_device", "cap")],
    "boundary_random_write_bit": [("device", "cap")],
    "boundary_random_write_word_ext": [("word_device", "cap")],
    "boundary_random_write_word_weighted_ext": [("dword_device", "cap")],
    "boundary_random_write_bit_ext": [("device", "cap")],
    "block_write": [("word_device", "word_points"), ("bit_device", "bit_points")],
}

RANDOM_TYPES = {
    "boundary_random_read_word",
    "boundary_random_write_word",
    "boundary_random_write_word_weighted",
    "boundary_random_write_bit",
    "boundary_random_read_word_ext",
    "boundary_random_write_word_ext",
    "boundary_random_write_word_weighted_ext",
    "boundary_random_write_bit_ext",
    "boundary_monitor_register",
    "boundary_monitor_register_ext",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def markdown_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(markdown_cell(cell) for cell in row) + " |")
    return lines


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def result_target(item: dict[str, Any]) -> str:
    for key in ("device", "word_device", "dword_device"):
        if item.get(key):
            return str(item[key])
    if item.get("routes"):
        return "qualified routes"
    if item.get("families"):
        return "device families"
    return ""


def result_summary(item: dict[str, Any]) -> str:
    parts: list[str] = []
    if item.get("text"):
        parts.append(f"text={item['text']}")
    if item.get("end_code") is not None:
        parts.append(f"end={item['end_code']}")
    if item.get("end_codes"):
        parts.append("ends=" + ",".join(item["end_codes"]))
    if item.get("status"):
        parts.append(f"status={item['status']}")
    if item.get("largest_pass") is not None:
        parts.append(f"largest_pass={item['largest_pass']}")
    if item.get("first_fail") is not None:
        parts.append(f"first_fail={item['first_fail']}")
    if item.get("fail_end"):
        parts.append(f"fail_end={item['fail_end']}")
    if item.get("no_fail_up_to_cap") is not None:
        parts.append(f"no_fail_up_to_cap={item['no_fail_up_to_cap']}")
    if item.get("error"):
        parts.append(f"error={item['error']}")
    return "; ".join(parts)


def render_summary_markdown(summary: dict[str, Any], result_path: Path) -> str:
    profile = summary.get("profile", {})
    plan = summary.get("plan", "")
    plan_display = str(plan).replace("\\", "/")
    title = Path(plan_display).stem if plan_display else result_path.stem
    rows = summary.get("results", [])
    waived = summary.get("waived", [])
    errors = summary.get("errors", [])

    lines: list[str] = [
        "<!-- Generated by tools/run_unit_probe_plan.py. Do not edit manually. -->",
        "",
        f"# {title} Unit Probe Result",
        "",
        "This is a generated human-readable view of the canonical result JSON.",
        "",
    ]
    lines.extend(
        markdown_table(
            ["Item", "Value"],
            [
                ["Plan", plan_display],
                ["Result JSON", display_path(result_path)],
                ["Profile", profile.get("profile", "")],
                ["Frame", profile.get("frame", "")],
                ["Compatibility", profile.get("compat", "")],
                ["Target", summary.get("target", "")],
                ["Items", f"{summary.get('recorded_items', 0)}/{summary.get('started_items', 0)}"],
                ["Waived", ", ".join(waived) if waived else "none"],
                ["Errors", ", ".join(errors) if errors else "none"],
            ],
        )
    )

    boundary_rows: list[list[Any]] = []
    route_rows: list[list[Any]] = []
    family_rows: list[list[Any]] = []
    core_rows: list[list[Any]] = []

    for item in rows:
        item_id = str(item.get("id", ""))
        if item_id.startswith("boundary_"):
            boundary_rows.append(
                [
                    item_id,
                    item.get("type", ""),
                    result_target(item),
                    item.get("status", ""),
                    item.get("largest_pass", ""),
                    item.get("first_fail", item.get("no_fail_up_to_cap", "")),
                    item.get("fail_end", ""),
                ]
            )
        elif item_id == "ext_read_routes":
            for route, end_code in item.get("routes", {}).items():
                route_rows.append([route, end_code])
        elif item_id == "family_reachability":
            for family, entry in item.get("families", {}).items():
                if isinstance(entry, dict):
                    note = entry.get("note", "")
                    if entry.get("raw_device_code_probe"):
                        note = f"{note}; raw device code probe".strip("; ")
                    family_rows.append(
                        [family, entry.get("device", ""), entry.get("access", ""), entry.get("end_code", ""), note]
                    )
                else:
                    family_rows.append([family, "", "", entry, "legacy result shape"])
        else:
            core_rows.append([item_id, item.get("type", item.get("status", "")), result_target(item), result_summary(item)])

    if core_rows:
        lines += ["", "## Core Items", ""]
        lines.extend(markdown_table(["ID", "Type", "Target", "Result"], core_rows))
    if boundary_rows:
        lines += ["", "## Boundaries", ""]
        lines.extend(markdown_table(["ID", "Type", "Target", "Status", "Largest pass", "Fail/no-fail point", "End"], boundary_rows))
    if route_rows:
        lines += ["", "## Qualified Routes", ""]
        lines.extend(markdown_table(["Route", "End code"], route_rows))
    if family_rows:
        lines += ["", "## Device Families", ""]
        lines.extend(markdown_table(["Family", "Device", "Access", "End code", "Note"], family_rows))
    lines.append("")
    return "\n".join(lines)


def route_family(route_device: str) -> str:
    text = route_device.strip().upper()
    if "\\" in text or "/" in text:
        sep = "\\" if "\\" in text else "/"
        _, raw = text.split(sep, 1)
    else:
        raw = text
    code, _ = probe.parse_device(raw)
    return code


class PlanError(Exception):
    pass


class Runner:
    def __init__(self, plan_path: Path, out_dir: Path | None) -> None:
        self.plan_path = plan_path
        self.plan = load_json(plan_path)
        self.manifest = load_json(MANIFEST_PATH)
        conn = self.plan.get("connection", {})
        self.conn = SimpleNamespace(
            host=conn.get("host", "192.168.250.100"),
            port=int(conn.get("port", 1025)),
            timeout=float(conn.get("timeout", 10.0)),
        )
        self.frame_opts = {
            "monitoring_timer": int(conn.get("monitoring_timer", 0x0010)),
            "network": int(conn.get("network", 0x00)),
            "station": int(conn.get("station", 0xFF)),
            "module_io": int(conn.get("module_io", 0x03FF)),
            "multidrop": int(conn.get("multidrop", 0x00)),
        }
        prof = self.plan["profile"]
        self.profile = probe.load_probe_profile(
            SimpleNamespace(
                profile=prof["base"],
                frame=prof.get("frame"),
                compat=prof.get("compat"),
                word_subcommand=None,
                bit_subcommand=None,
                ext_word_subcommand=None,
                ext_bit_subcommand=None,
            )
        )
        self.items: list[dict[str, Any]] = self.plan["items"]
        self.write_allow: dict[str, int] = {
            entry["device"].strip().upper(): int(entry["span"]) for entry in self.plan.get("write_allow", [])
        }
        self.results_path = (
            out_dir / "results.json"
            if out_dir is not None
            else self.plan_path.parent / "results" / f"{self.plan.get('name', self.plan_path.stem)}.json"
        )
        self.summary_path = self.results_path.with_suffix(".md")
        self.results: list[dict[str, Any]] = []

    # ---------------- validation ----------------

    def validate(self) -> list[str]:
        problems: list[str] = []
        by_id = {item["id"]: item for item in self.items}
        if len(by_id) != len(self.items):
            problems.append("duplicate item ids in plan")

        for item_id, expected_type in self.manifest["required_items"].items():
            item = by_id.get(item_id)
            if item is None:
                problems.append(f"missing required item: {item_id} (type {expected_type})")
                continue
            if "waiver" in item:
                if not str(item["waiver"]).strip():
                    problems.append(f"item {item_id}: waiver must be a non-empty reason")
                continue
            if item.get("type") != expected_type:
                problems.append(f"item {item_id}: type must be {expected_type}, got {item.get('type')}")

        for item in self.items:
            if "waiver" in item:
                continue
            item_type = item.get("type", "")
            for param, need in WRITE_PARAMS.get(item_type, []):
                target = item.get("params", {}).get(param)
                if target is None:
                    continue  # optional half of a block item
                span_needed = 1
                if need == "cap":
                    span_needed = int(item["params"].get("cap", 1)) + 1
                elif need != "one":
                    span_needed = int(item["params"].get(need, 1)) + 1
                allowed = self.write_allow.get(str(target).strip().upper())
                if allowed is None:
                    problems.append(f"item {item['id']}: write target {target!r} is not in write_allow")
                elif allowed < span_needed:
                    problems.append(
                        f"item {item['id']}: write_allow span for {target!r} is {allowed}, needs >= {span_needed}"
                    )
            if item_type in RANDOM_TYPES:
                cap = int(item.get("params", {}).get("cap", RANDOM_FIELD_CAP))
                if cap > RANDOM_FIELD_CAP:
                    problems.append(f"item {item['id']}: cap {cap} exceeds one-byte count field limit {RANDOM_FIELD_CAP}")

        routes_item = by_id.get("ext_read_routes")
        if routes_item is not None and "waiver" not in routes_item:
            routes: dict[str, str] = routes_item.get("params", {}).get("routes", {})
            for required in self.manifest["required_ext_read_routes"]:
                if required not in routes:
                    problems.append(f"ext_read_routes: missing required route {required}")

        fam_item = by_id.get("family_reachability")
        if fam_item is not None and "waiver" not in fam_item:
            overrides = fam_item.get("params", {}).get("overrides", {})
            unknown = set(overrides) - set(self.manifest["required_families"])
            if unknown:
                problems.append(f"family_reachability: unknown families in overrides: {sorted(unknown)}")
        return problems

    def describe(self) -> None:
        print(f"plan: {self.plan_path}")
        print(f"target: {self.conn.host}:{self.conn.port} timeout={self.conn.timeout}s")
        print(f"profile: {self.profile.name} frame={self.profile.frame} compat={self.profile.compat}")
        print(f"items: {len(self.items)} (required: {len(self.manifest['required_items'])})")
        writes = sorted(self.write_allow.items())
        print("write_allow:")
        for device, span in writes:
            print(f"  {device}  span={span}")
        for item in self.items:
            mark = "WAIVED" if "waiver" in item else item.get("type", "?")
            print(f"  - {item['id']}  [{mark}]")

    # ---------------- low-level probing ----------------

    def _log(self, row: dict[str, Any]) -> None:
        return

    def _exchange(
        self,
        item_id: str,
        label: str,
        requests: list[tuple[int, int, bytes]],
        stop_on_nonzero: bool = True,
        capture_data: bool = False,
    ) -> list[dict[str, Any]]:
        """Send requests on one socket and return per-request rows."""
        rows: list[dict[str, Any]] = []
        for retry in (0, 1):
            try:
                with probe.open_socket(self.conn) as sock:
                    for index, (command, subcommand, data) in enumerate(requests, start=1):
                        frame = probe.request_frame(
                            self.profile,
                            command,
                            subcommand,
                            data,
                            serial=index,
                            **self.frame_opts,
                        )
                        response = probe.send_request(sock, self.profile, frame)
                        row = {
                            "item": item_id,
                            "label": label,
                            "seq": index,
                            "command": f"{command:04X}",
                            "subcommand": f"{subcommand:04X}",
                            "end_code": f"{response.end_code:04X}",
                            "data_bytes": len(response.data),
                            "retry": retry,
                        }
                        if capture_data:
                            row["data_hex"] = response.data.hex()
                        rows.append(row)
                        self._log(row)
                        if stop_on_nonzero and response.end_code != 0:
                            return rows
                return rows
            except Exception as exc:  # noqa: BLE001 -- record and retry once; never silently drop an attempt
                row = {
                    "item": item_id,
                    "label": label,
                    "error": type(exc).__name__,
                    "detail": str(exc) or type(exc).__name__,
                    "retry": retry,
                }
                rows = [row]
                self._log(row)
                if retry == 0:
                    time.sleep(1.0)
        return rows

    def _end_code(self, rows: list[dict[str, Any]]) -> str | None:
        for row in rows:
            if "error" not in row:
                return row["end_code"]
        return None

    def _response_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [row for row in rows if "error" not in row]

    # ---------------- boundary search ----------------

    def _search_boundary(self, item_id: str, probe_fn: Callable[[int], list[dict[str, Any]]], cap: int) -> dict[str, Any]:
        def attempt(count: int) -> str | None:
            rows = probe_fn(count)
            code = self._end_code(rows)
            print(f"    {item_id}: count={count} -> {code if code is not None else 'ERROR'}", flush=True)
            return code

        count = 1
        last_pass = 0
        first_fail: int | None = None
        fail_code: str | None = None
        while count <= cap:
            code = attempt(count)
            if code is None:
                return {"status": "error", "at_count": count}
            if code == "0000":
                last_pass = count
                if count == cap:
                    break
                count = min(count * 2, cap)
            else:
                first_fail = count
                fail_code = code
                break
        if first_fail is None:
            return {"status": "limit", "largest_pass": last_pass, "no_fail_up_to_cap": cap}
        lo, hi = last_pass, first_fail
        while hi - lo > 1:
            mid = (lo + hi) // 2
            code = attempt(mid)
            if code is None:
                return {"status": "error", "at_count": mid}
            if code == "0000":
                lo = mid
            else:
                hi = mid
                fail_code = code
        if lo == 0:
            return {"status": "fail", "first_fail": hi, "fail_end": fail_code}
        return {"status": "limit", "largest_pass": lo, "first_fail": hi, "fail_end": fail_code}

    # ---------------- item executors ----------------

    def _word_value(self, params: dict[str, Any]) -> int:
        return int(params.get("word_value", 0x2222))

    def _dword_value(self, params: dict[str, Any]) -> int:
        return int(params.get("dword_value", 0x33334444))

    def run_item(self, item: dict[str, Any]) -> dict[str, Any]:
        item_id = item["id"]
        params: dict[str, Any] = item.get("params", {})
        item_type = item["type"]
        p = self.profile
        sub = p.subcommands

        def ex(label: str, requests: list[tuple[int, int, bytes]], stop_on_nonzero: bool = True) -> list[dict[str, Any]]:
            return self._exchange(item_id, label, requests, stop_on_nonzero)

        if item_type == "type_name":
            rows = self._exchange(item_id, "type-name", [(probe.COMMAND_TYPE_NAME, 0x0000, b"")], capture_data=True)
            result: dict[str, Any] = {"end_code": self._end_code(rows)}
            response_rows = self._response_rows(rows)
            if result["end_code"] == "0000" and response_rows and response_rows[0].get("data_hex"):
                data = bytes.fromhex(response_rows[0]["data_hex"])
                result["raw_hex"] = response_rows[0]["data_hex"]
                result["text"] = data[:16].rstrip(b"\x00 ").decode("ascii", errors="replace")
                if len(data) >= 18:
                    result["type_code_hex"] = data[16:18].hex()
            return result

        if item_type in ("read_word", "read_bit"):
            bit = item_type == "read_bit"
            data = probe.device_payload(p, params["device"], int(params.get("points", 1)))
            rows = ex(item_type, [(probe.COMMAND_DEVICE_READ, sub["bit" if bit else "word"], data)])
            return {"device": params["device"], "end_code": self._end_code(rows)}

        if item_type == "write_word_verify":
            device = params["device"]
            value = self._word_value(params)
            rows = ex(
                "write+readback",
                [
                    (probe.COMMAND_DEVICE_WRITE, sub["word"], probe.device_payload(p, device, 1, probe.pack_words([value]))),
                    (probe.COMMAND_DEVICE_READ, sub["word"], probe.device_payload(p, device, 1)),
                ],
            )
            return {"device": device, "value": value, "end_codes": [r["end_code"] for r in self._response_rows(rows)]}

        if item_type == "write_bit_verify":
            device = params["device"]
            rows = ex(
                "write+read+reset+read",
                [
                    (probe.COMMAND_DEVICE_WRITE, sub["bit"], probe.device_payload(p, device, 1, probe.pack_bits([True]))),
                    (probe.COMMAND_DEVICE_READ, sub["bit"], probe.device_payload(p, device, 1)),
                    (probe.COMMAND_DEVICE_WRITE, sub["bit"], probe.device_payload(p, device, 1, probe.pack_bits([False]))),
                    (probe.COMMAND_DEVICE_READ, sub["bit"], probe.device_payload(p, device, 1)),
                ],
            )
            return {"device": device, "end_codes": [r["end_code"] for r in self._response_rows(rows)]}

        if item_type in ("boundary_direct_read_word", "boundary_direct_read_bit"):
            bit = item_type.endswith("bit")
            device = params["device"]
            cap = int(params["cap"])

            def fn(count: int) -> list[dict[str, Any]]:
                data = probe.device_payload(p, device, count)
                return ex(f"count={count}", [(probe.COMMAND_DEVICE_READ, sub["bit" if bit else "word"], data)])

            return {"device": device, **self._search_boundary(item_id, fn, cap)}

        if item_type == "boundary_direct_write_word":
            device = params["device"]
            cap = int(params["cap"])
            value = self._word_value(params)

            def fn(count: int) -> list[dict[str, Any]]:
                data = probe.device_payload(p, device, count, probe.pack_words([value] * count))
                return ex(f"count={count}", [(probe.COMMAND_DEVICE_WRITE, sub["word"], data)])

            return {"device": device, **self._search_boundary(item_id, fn, cap)}

        if item_type == "boundary_direct_write_bit":
            device = params["device"]
            cap = int(params["cap"])

            def fn(count: int) -> list[dict[str, Any]]:
                write = probe.device_payload(p, device, count, probe.pack_bits([True] * count))
                reset = probe.device_payload(p, device, count, probe.pack_bits([False] * count))
                rows = ex(f"count={count}", [(probe.COMMAND_DEVICE_WRITE, sub["bit"], write)])
                if self._end_code(rows) == "0000":
                    ex(f"count={count} reset", [(probe.COMMAND_DEVICE_WRITE, sub["bit"], reset)])
                return rows

            return {"device": device, **self._search_boundary(item_id, fn, cap)}

        if item_type in ("boundary_random_read_word", "boundary_random_read_word_ext"):
            ext = item_type.endswith("_ext")
            template = params["word_device"]
            cap = int(params.get("cap", RANDOM_FIELD_CAP))
            gen = probe.generated_devices if ext else probe.generated_plain_devices
            payload_fn = probe.random_read_ext_payload if ext else probe.random_read_payload
            subcommand = sub["ext_word" if ext else "word"]

            def fn(count: int) -> list[dict[str, Any]]:
                data = payload_fn(p, gen(template, count), [])
                return ex(f"count={count}", [(probe.COMMAND_DEVICE_READ_RANDOM, subcommand, data)])

            return {"word_device": template, **self._search_boundary(item_id, fn, cap)}

        if item_type in ("boundary_random_write_word", "boundary_random_write_word_ext"):
            ext = item_type.endswith("_ext")
            template = params["word_device"]
            cap = int(params.get("cap", RANDOM_FIELD_CAP))
            value = self._word_value(params)
            gen = probe.generated_devices if ext else probe.generated_plain_devices
            payload_fn = probe.random_write_words_ext_payload if ext else probe.random_write_words_payload
            subcommand = sub["ext_word" if ext else "word"]

            def fn(count: int) -> list[dict[str, Any]]:
                data = payload_fn(p, gen(template, count), [], word_value=value, dword_value=0)
                return ex(f"count={count}", [(probe.COMMAND_DEVICE_WRITE_RANDOM, subcommand, data)])

            return {"word_device": template, **self._search_boundary(item_id, fn, cap)}

        if item_type in ("boundary_random_write_word_weighted", "boundary_random_write_word_weighted_ext"):
            ext = item_type.endswith("_ext")
            template = params["dword_device"]
            cap = int(params.get("cap", RANDOM_FIELD_CAP))
            value = self._dword_value(params)
            gen = probe.generated_devices if ext else probe.generated_plain_devices
            payload_fn = probe.random_write_words_ext_payload if ext else probe.random_write_words_payload
            subcommand = sub["ext_word" if ext else "word"]

            def fn(count: int) -> list[dict[str, Any]]:
                data = payload_fn(p, [], gen(template, count), word_value=0, dword_value=value)
                return ex(f"dword_count={count}", [(probe.COMMAND_DEVICE_WRITE_RANDOM, subcommand, data)])

            return {"dword_device": template, **self._search_boundary(item_id, fn, cap)}

        if item_type in ("boundary_random_write_bit", "boundary_random_write_bit_ext"):
            ext = item_type.endswith("_ext")
            template = params["device"]
            cap = int(params.get("cap", RANDOM_FIELD_CAP))
            gen = probe.generated_devices if ext else probe.generated_plain_devices
            payload_fn = probe.random_write_bits_ext_payload if ext else probe.random_write_bits_payload
            subcommand = sub["ext_bit" if ext else "bit"]

            def fn(count: int) -> list[dict[str, Any]]:
                devices = gen(template, count)
                rows = ex(f"count={count}", [(probe.COMMAND_DEVICE_WRITE_RANDOM, subcommand, payload_fn(p, devices, True))])
                if self._end_code(rows) == "0000":
                    ex(f"count={count} reset", [(probe.COMMAND_DEVICE_WRITE_RANDOM, subcommand, payload_fn(p, devices, False))])
                return rows

            return {"device": template, **self._search_boundary(item_id, fn, cap)}

        if item_type in ("boundary_monitor_register", "boundary_monitor_register_ext"):
            ext = item_type.endswith("_ext")
            template = params["word_device"]
            cap = int(params.get("cap", RANDOM_FIELD_CAP))
            gen = probe.generated_devices if ext else probe.generated_plain_devices
            payload_fn = probe.random_read_ext_payload if ext else probe.random_read_payload
            subcommand = sub["ext_word" if ext else "word"]

            def fn(count: int) -> list[dict[str, Any]]:
                data = payload_fn(p, gen(template, count), [])
                return ex(f"count={count}", [(probe.COMMAND_DEVICE_ENTRY_MONITOR, subcommand, data)])

            return {"word_device": template, **self._search_boundary(item_id, fn, cap)}

        if item_type == "monitor_execute":
            template = params["word_device"]
            data = probe.random_read_payload(p, probe.generated_plain_devices(template, 1), [])
            rows = ex(
                "register+execute",
                [
                    (probe.COMMAND_DEVICE_ENTRY_MONITOR, sub["word"], data),
                    (probe.COMMAND_DEVICE_EXECUTE_MONITOR, sub["word"], b""),
                ],
            )
            return {"word_device": template, "end_codes": [r["end_code"] for r in self._response_rows(rows)]}

        if item_type == "block_read":
            data = probe.block_access_payload(
                p,
                word_device=params.get("word_device"),
                word_points=int(params.get("word_points", 0)),
                bit_device=params.get("bit_device"),
                bit_points=int(params.get("bit_points", 0)),
            )
            rows = ex("block-read", [(probe.COMMAND_DEVICE_READ_BLOCK, sub["word"], data)])
            return {"end_code": self._end_code(rows)}

        if item_type == "block_write":
            word_points = int(params.get("word_points", 0))
            bit_points = int(params.get("bit_points", 0))
            word_data = probe.pack_words([self._word_value(params)] * word_points) if params.get("word_device") else b""
            bit_data = probe.pack_words([0xFFFF] * bit_points) if params.get("bit_device") else b""
            data = probe.block_access_payload(
                p,
                word_device=params.get("word_device"),
                word_points=word_points,
                bit_device=params.get("bit_device"),
                bit_points=bit_points,
                word_data=word_data,
                bit_data=bit_data,
            )
            rows = ex("block-write", [(probe.COMMAND_DEVICE_WRITE_BLOCK, sub["word"], data)])
            if self._end_code(rows) == "0000" and params.get("bit_device"):
                reset = probe.block_access_payload(
                    p,
                    word_device=None,
                    word_points=0,
                    bit_device=params["bit_device"],
                    bit_points=bit_points,
                    bit_data=probe.pack_words([0] * bit_points),
                )
                ex("block-write reset", [(probe.COMMAND_DEVICE_WRITE_BLOCK, sub["word"], reset)])
            return {"end_code": self._end_code(rows)}

        if item_type == "ext_read_routes":
            routes: dict[str, str] = params["routes"]
            outcome: dict[str, str | None] = {}
            for route_key, device in routes.items():
                family = route_family(device)
                bit = family in {"X", "Y", "B", "SB", "M", "L", "F", "V", "S", "SM"}
                data = probe.extended_device_payload(p, device, 1)
                rows = ex(
                    f"route {route_key} ({device})",
                    [(probe.COMMAND_DEVICE_READ, sub["ext_bit" if bit else "ext_word"], data)],
                )
                outcome[route_key] = self._end_code(rows)
            return {"routes": outcome}

        if item_type == "family_reachability":
            overrides: dict[str, str] = params.get("overrides", {})
            outcome = {}
            for family, spec in self.manifest["required_families"].items():
                device = overrides.get(family, spec["device"])
                access = spec["access"]
                if access == "dword_random":
                    data = probe.random_read_payload(p, [], [device])
                    rows = ex(f"family {family} ({device})", [(probe.COMMAND_DEVICE_READ_RANDOM, sub["word"], data)])
                elif access == "word4":  # intended long route: one 4-word unit
                    data = probe.device_payload(p, device, 4)
                    rows = ex(f"family {family} ({device} x4)", [(probe.COMMAND_DEVICE_READ, sub["word"], data)])
                else:
                    data = probe.device_payload(p, device, 1)
                    rows = ex(
                        f"family {family} ({device})",
                        [(probe.COMMAND_DEVICE_READ, sub["bit" if access == "bit" else "word"], data)],
                    )
                entry: dict[str, Any] = {
                    "device": device,
                    "access": access,
                    "end_code": self._end_code(rows),
                }
                if spec.get("raw"):
                    entry["raw_device_code_probe"] = True  # library never sends this code; record only
                if spec.get("note"):
                    entry["note"] = spec["note"]
                outcome[family] = entry
            return {"families": outcome}

        raise PlanError(f"unknown item type: {item_type}")

    # ---------------- orchestration ----------------

    @staticmethod
    def _outcome_failed(outcome: dict[str, Any]) -> bool:
        """True when an item has an unmeasured hole (an all-retries-failed request)."""
        if outcome.get("status") == "error":
            return True
        if outcome.get("status") in ("limit", "fail"):
            return False
        if "end_code" in outcome and outcome["end_code"] is None:
            return True
        if "end_codes" in outcome and not outcome["end_codes"]:
            return True
        if "routes" in outcome and any(code is None for code in outcome["routes"].values()):
            return True
        if "families" in outcome and any(entry.get("end_code") is None for entry in outcome["families"].values()):
            return True
        return False

    def run(self) -> int:
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        errors = 0
        total = len(self.items)
        for index, item in enumerate(self.items, start=1):
            item_id = item["id"]
            if "waiver" in item:
                print(f"[{index}/{total}] {item_id}: WAIVED ({item['waiver']})", flush=True)
                self.results.append({"id": item_id, "status": "waived", "waiver": item["waiver"]})
                continue
            print(f"[{index}/{total}] {item_id} ({item['type']})", flush=True)
            try:
                outcome = self.run_item(item)
            except Exception as exc:  # noqa: BLE001 -- an item failure must become a row, not an abort
                outcome = {"status": "error", "error": type(exc).__name__, "detail": str(exc)}
            if self._outcome_failed(outcome):
                outcome["status"] = "error"
                errors += 1
            self.results.append({"id": item_id, "type": item["type"], **outcome})
        summary = {
            "plan": str(self.plan_path),
            "profile": probe.profile_context(self.profile),
            "target": f"{self.conn.host}:{self.conn.port}",
            "started_items": len(self.items),
            "recorded_items": len(self.results),
            "waived": [r["id"] for r in self.results if r.get("status") == "waived"],
            "errors": [r["id"] for r in self.results if r.get("status") == "error"],
            "results": self.results,
        }
        self.results_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=False), encoding="utf-8")
        self.summary_path.write_text(render_summary_markdown(summary, self.results_path), encoding="utf-8", newline="\n")
        print(f"\nresults: {self.results_path}")
        print(f"summary: {self.summary_path}")
        print(f"items recorded: {len(self.results)}/{len(self.items)}  waived: {len(summary['waived'])}  errors: {len(summary['errors'])}")
        if len(self.results) != len(self.items):
            return 3
        return 3 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan-driven unit probe sweep (no operator discretion).")
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Validate the plan and list items; no communication.")
    args = parser.parse_args()

    runner = Runner(args.plan, args.out_dir)
    problems = runner.validate()
    if problems:
        print("PLAN VALIDATION FAILED — fix the plan; skipping items at runtime is not possible:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2
    if args.dry_run:
        runner.describe()
        print("dry-run OK: plan is complete and executable")
        return 0
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
