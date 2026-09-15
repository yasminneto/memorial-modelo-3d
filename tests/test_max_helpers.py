"""Portable math/contract tests; these do NOT certify the native 3ds Max API."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock


ADAPTER = (Path(__file__).resolve().parents[1] / "plugins" / "memorial-modelo-3d"
           / "skills" / "memorial-modelo-3d" / "adapters" / "3dsmax"
           / "export_manifest.py")
SPEC = importlib.util.spec_from_file_location("max_adapter", ADAPTER)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def point(x, y, z):
    return SimpleNamespace(x=x, y=y, z=z)


class MaxHelperTests(unittest.TestCase):
    def test_system_scale_not_only_unit_label(self):
        cases = [("millimeters", 1, 0.001), ("#Inches", 100, 2.54),
                 ("feet", 2, 0.6096), ("Meters", 0.5, 0.5)]
        for system_type, multiplier, expected in cases:
            with self.subTest(system_type=system_type, multiplier=multiplier):
                self.assertAlmostEqual(MODULE.unit_scale_to_m(system_type, multiplier), expected)

    def test_unknown_system_units_fail_instead_of_assuming_meters(self):
        for value in ("generic", "custom", "", "parsecs"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MODULE.unit_scale_to_m(value, 1)

    def test_invalid_scales_fail(self):
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    MODULE.unit_scale_to_m("meters", value)

    def test_world_bounds_preserve_translation_and_negative_positions(self):
        actual = MODULE._bounds([point(-1000, 2000, -500), point(1000, 6000, 2500)], 0.001)
        self.assertEqual(actual, {"min": [-1.0, 2.0, -0.5], "max": [1.0, 6.0, 2.5]})

    def test_invalid_bounds_fail_instead_of_producing_fake_measurements(self):
        cases = [[point(2, 0, 0), point(1, 1, 1)],
                 [point(float("nan"), 0, 0), point(1, 1, 1)],
                 [point(0, 0, 0), point(float("inf"), 1, 1)]]
        for bounds in cases:
            with self.subTest(bounds=bounds):
                with self.assertRaises(ValueError):
                    MODULE._bounds(bounds, 1)

    def test_unsaved_scene_rejected_before_api_geometry_access(self):
        with self.assertRaisesRegex(RuntimeError, "saved .max working copy"):
            MODULE.extract_manifest(rt=SimpleNamespace(maxFileName=""), mxs=object())

    def test_cannot_write_model_or_existing_manifest(self):
        with mock.patch.object(MODULE, "extract_manifest") as extract:
            with self.assertRaises(ValueError):
                MODULE.export_manifest("never-write.max")
            with mock.patch.object(MODULE.os.path, "exists", return_value=True):
                with self.assertRaises(FileExistsError):
                    MODULE.export_manifest("existing.json")
            extract.assert_not_called()


if __name__ == "__main__":
    unittest.main()
