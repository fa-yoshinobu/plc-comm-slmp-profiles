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
- Every request attempt is appended to attempts.jsonl immediately
  (flushed), and the run ends with a completeness summary. Exit codes:
  0 = complete, 2 = plan validation failed, 3 = completed with errors.

Usage:
  python tools/run_unit_probe_plan.py --plan <plan.json> [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

TOOLS_DIR = Path(__file__).resolve().parent
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
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.out_dir = out_dir or (
            self.plan_path.parent / "runs" / f"{self.plan.get('name', self.plan_path.stem)}_{stamp}"
        )
        self.attempts_fh = None
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
        assert self.attempts_fh is not None
        self.attempts_fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        self.attempts_fh.flush()

    def _exchange(
        self,
        item_id: str,
        label: str,
        requests: list[tuple[int, int, bytes]],
        stop_on_nonzero: bool = True,
    ) -> list[dict[str, Any]]:
        """Send requests on one socket; log every attempt; return per-request rows."""
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
        if not rows or "error" in rows[0]:
            return None
        return rows[0]["end_code"]

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
            rows = ex("type-name", [(probe.COMMAND_TYPE_NAME, 0x0000, b"")])
            return {"end_code": self._end_code(rows)}

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
            return {"device": device, "value": value, "end_codes": [r.get("end_code") for r in rows]}

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
            return {"device": device, "end_codes": [r.get("end_code") for r in rows]}

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
            return {"word_device": template, "end_codes": [r.get("end_code") for r in rows]}

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
                else:
                    data = probe.device_payload(p, device, 1)
                    rows = ex(
                        f"family {family} ({device})",
                        [(probe.COMMAND_DEVICE_READ, sub["bit" if access == "bit" else "word"], data)],
                    )
                outcome[family] = self._end_code(rows)
            return {"families": outcome}

        raise PlanError(f"unknown item type: {item_type}")

    # ---------------- orchestration ----------------

    def run(self) -> int:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        attempts_path = self.out_dir / "attempts.jsonl"
        results_path = self.out_dir / "results.json"
        errors = 0
        with attempts_path.open("a", encoding="utf-8") as fh:
            self.attempts_fh = fh
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
                status = outcome.get("status")
                if status == "error" or (
                    status is None and outcome.get("end_code") is None and "end_codes" not in outcome
                    and "routes" not in outcome and "families" not in outcome
                ):
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
        results_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=False), encoding="utf-8")
        print(f"\nresults: {results_path}")
        print(f"attempts: {attempts_path}")
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
