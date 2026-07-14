from __future__ import annotations

import unittest
from pathlib import Path

from run_unit_probe_plan import render_summary_markdown


class SummaryPathTests(unittest.TestCase):
    def render(self, plan: str) -> str:
        summary = {
            "plan": plan,
            "profile": {},
            "results": [],
            "waived": [],
            "errors": [],
        }
        return render_summary_markdown(summary, Path("results/example.json"))

    def test_windows_plan_path_has_stable_title(self) -> None:
        rendered = self.render(r"evidence\unit-investigations\plans\mx-r.json")

        self.assertIn("# mx-r Unit Probe Result", rendered)
        self.assertIn("evidence/unit-investigations/plans/mx-r.json", rendered)

    def test_posix_plan_path_has_stable_title(self) -> None:
        rendered = self.render("evidence/unit-investigations/plans/mx-r.json")

        self.assertIn("# mx-r Unit Probe Result", rendered)
        self.assertIn("evidence/unit-investigations/plans/mx-r.json", rendered)


if __name__ == "__main__":
    unittest.main()
