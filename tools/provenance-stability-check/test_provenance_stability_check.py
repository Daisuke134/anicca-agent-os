"""CLI contract and fail-closed reporting tests; standard library only."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "provenance_stability_check.py"
PREFIX = 'PS'
CONTROL = ['PS-3', 'PS-4']

class GateTests(unittest.TestCase):
    def run_cli(self, path):
        return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)

    def test_fixture_contract(self):
        for name, failed in [("compliant", []), ("anicca-current", [f"{PREFIX}-{i}" for i in range(6)]), ("control", CONTROL)]:
            with self.subTest(name=name):
                run = self.run_cli(ROOT / "fixtures" / (name + ".json"))
                self.assertEqual(run.returncode, int(bool(failed)), run.stderr)
                output = json.loads(run.stdout)
                self.assertEqual(output["failed_gates"], failed)
                self.assertEqual(output["passed"], 6-len(failed))
                self.assertEqual(output["failed"], len(failed))
                self.assertEqual(output["total"], 6)
                self.assertEqual(len(output["gates"]), 6)
                self.assertEqual(run.stdout, self.run_cli(ROOT / "fixtures" / (name + ".json")).stdout)

    def test_invalid_input_fails_with_all_gates(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            path = Path(temporary) / "input.json"
            for content in ['[]', '{', '{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{}']:
                path.write_text(content)
                run = self.run_cli(path)
                self.assertEqual(run.returncode, 1)
                self.assertEqual(json.loads(run.stdout)["failed"], 6)
            self.assertEqual(self.run_cli(Path(temporary)/"missing.json").returncode, 1)

    def test_required_fields_fail_when_deleted_or_null(self):
        spec = importlib.util.spec_from_file_location("checker", SCRIPT)
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        original = json.loads((ROOT / "fixtures/compliant.json").read_text())
        # Every leaf and container in the fully applicable design is required,
        # except annotations and optional non-attribute provenance fields.
        def paths(node, prefix=()):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key != "fixture_note":
                        yield prefix + (key,)
                        yield from paths(value, prefix + (key,))
            elif isinstance(node, list):
                for i, value in enumerate(node):
                    yield from paths(value, prefix + (i,))
        for path in paths(original):
            for remove in (False, True):
                with self.subTest(path=path, remove=remove):
                    state = copy.deepcopy(original)
                    node = state
                    for key in path[:-1]:
                        node = node[key]
                    if remove:
                        del node[path[-1]]
                    else:
                        node[path[-1]] = None
                    self.assertFalse(all(checker.check(state).values()))

    def load_checker(self):
        spec = importlib.util.spec_from_file_location("checker", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_malformed_top_level_fields_never_crash_or_pass(self):
        checker = self.load_checker()
        original = json.loads((ROOT / "fixtures/compliant.json").read_text())
        for key in original:
            if key == "fixture_note":
                continue
            for bad in (None, [], {}, "", 42, True):
                state = copy.deepcopy(original)
                state[key] = bad
                with self.subTest(key=key, bad=bad):
                    result = checker.check(state)
                    self.assertEqual(len(result), 6)
                    # Boolean True can be a valid original declaration.
                    if bad != original[key]:
                        self.assertFalse(all(result.values()))

    def test_numbers_are_finite_and_not_booleans(self):
        checker = self.load_checker()
        for bad in (True, False, "0.5", None, float("inf"), float("nan")):
            self.assertFalse(checker.number(bad))
        self.assertTrue(checker.number(0))
        self.assertTrue(checker.number(-0.8))

    def test_conditional_claims_and_audit_boundaries(self):
        checker = self.load_checker()
        state = json.loads((ROOT / "fixtures/compliant.json").read_text())
        for key, gate in [("predictive_claim", "PS-5"), ("realism_claim", "PS-4")]:
            state.pop("human_studies" if key == "predictive_claim" else "human_calibration_reference")
            for value, expected in [(False, True), (None, False), (0, False), ("false", False), (True, False)]:
                state[key] = value
                self.assertEqual(checker.check(state)[gate], expected)
        attribute = state["claims"][1]
        for verdict, expected in [("supported", True), ("partially_supported", True), ("unsupported", True), ("unflagged", False), ("unknown", False)]:
            attribute["audit"] = verdict
            self.assertEqual(checker.check(state)["PS-3"], expected)
        state["claims"][1] = {"type":"attribute", "population":"adults", "enriched":False}
        self.assertTrue(checker.check(state)["PS-3"])
        del state["claims"][1]["enriched"]
        self.assertFalse(checker.check(state)["PS-3"])

    def test_revision_and_prediction_consistency(self):
        checker = self.load_checker()
        state = json.loads((ROOT / "fixtures/compliant.json").read_text())
        state["stability_audit"]["revisions"][0]["type"] = "multimodal"
        self.assertFalse(checker.check(state)["PS-1"])
        state["human_studies"]["minimum_correlation"] = 0.8
        self.assertFalse(checker.check(state)["PS-5"])
        state["human_studies"]["minimum_correlation"] = 0.6
        state["human_studies"]["fitted_not_forecast"] = False
        self.assertTrue(checker.check(state)["PS-5"])

if __name__ == "__main__":
    unittest.main()
