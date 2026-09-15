"""Portable regression tests; no SketchUp, Rhino or 3ds Max required."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace

SKILL = Path(__file__).resolve().parents[1] / "plugins/memorial-modelo-3d/skills/memorial-modelo-3d"
sys.path.insert(0, str(SKILL / "scripts"))
from memorial_core import ManifestError, create_spec, find_candidates, normalize_sketchup, read_json, validate_manifest, write_json
from memorial_cli import doctor


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.manifest = read_json(SKILL / "examples/manifest-demo.json")

    def test_demo_valid_and_explicitly_synthetic(self):
        self.assertEqual(validate_manifest(self.manifest), [])
        spec = create_spec(self.manifest, "Teste", ["demo:balcao-1"])
        self.assertTrue(spec["synthetic"])
        self.assertIsNone(spec["items"][0]["quantity"]["value"])
        self.assertEqual(spec["items"][0]["quantity"]["source"], "pending")
        self.assertEqual(spec["items"][0]["images"], [])
        self.assertIn("SINTÉTICA", spec["items"][0]["pending"][0])

    def test_wrong_unit_and_bad_scale_fail(self):
        self.manifest["source"]["units"] = "mm"
        self.assertTrue(validate_manifest(self.manifest))
        self.manifest["source"]["units"] = "m"
        for scale in (0, -1, True, float("nan"), float("inf"), "1"):
            self.manifest["source"]["unit_scale_to_m"] = scale
            self.assertTrue(validate_manifest(self.manifest), repr(scale))

    def test_nonfinite_and_reversed_bounds_fail(self):
        for bad in (float("nan"), float("inf"), True, "2", -1):
            current = copy.deepcopy(self.manifest)
            current["objects"][0]["world_bounds_m"]["max"][0] = bad
            self.assertTrue(validate_manifest(current), repr(bad))

    def test_duplicate_ids_and_bad_count_fail(self):
        self.manifest["objects"].append(copy.deepcopy(self.manifest["objects"][0]))
        errors = validate_manifest(self.manifest)
        self.assertTrue(any("duplicates" in error for error in errors))
        self.assertTrue(any("object_count" in error for error in errors))

    def test_missing_parent_and_cycle_fail(self):
        obj = self.manifest["objects"][0]
        obj["parent_id"] = "not-present"
        self.assertTrue(any("missing parent" in error for error in validate_manifest(self.manifest)))
        obj["parent_id"] = obj["id"]
        self.assertTrue(any("cycle" in error for error in validate_manifest(self.manifest)))

    def test_complete_cannot_hide_missing_data(self):
        self.manifest["extraction"]["status"] = "complete"
        self.assertTrue(validate_manifest(self.manifest))
        self.manifest["extraction"]["limitations"] = []
        self.assertEqual(validate_manifest(self.manifest), [])
        self.manifest["objects"][0]["world_bounds_m"] = None
        self.assertTrue(any("unavailable" in error for error in validate_manifest(self.manifest)))

    def test_malformed_entries_report_errors_without_crashing(self):
        self.manifest["objects"][0]["parent_id"] = []
        self.manifest["views"] = ["bad-view"]
        self.manifest["extraction"]["status"] = "complete"
        self.manifest["extraction"]["capabilities"] = [["bad-capability"]]
        self.assertGreater(len(validate_manifest(self.manifest)), 2)

    def test_extreme_bounds_cannot_overflow_dimension(self):
        self.manifest["objects"][0]["world_bounds_m"] = {"min": [-1e308, 0, 0], "max": [1e308, 1, 1]}
        self.assertTrue(validate_manifest(self.manifest))

    def test_nested_bounds_unavailable_in_legacy(self):
        legacy = {"schema_version": "1.0", "source_path": "fixture.skp", "sketchup_version": "2025",
                  "root_entities": [{"persistent_id": 10, "name": "Parent", "type": "Group", "world_bounds": {
                      "min_m": [10, 0, 0], "max_m": [12, 1, 1]}, "children": [
                          {"persistent_id": 11, "name": "Child", "world_bounds": {"min_m": [0, 0, 0], "max_m": [1, 1, 1]}}]}]}
        normalized = normalize_sketchup(legacy)
        self.assertEqual(normalized["objects"][0]["world_bounds_m"]["min"][0], 10)
        self.assertIsNone(normalized["objects"][1]["world_bounds_m"])
        self.assertEqual(normalized["objects"][1]["parent_id"], "sketchup:10")
        self.assertEqual(normalized["source"]["unit_scale_to_m"], 0.0254)
        self.assertEqual(normalized["extraction"]["status"], "partial")
        self.assertTrue(normalized["warnings"])

    def test_legacy_repeated_definition_paths_unique(self):
        child = {"persistent_id": 11, "name": "Same inner entity"}
        legacy = {"schema_version": "1.0", "source_path": "fixture.skp", "sketchup_version": "2025",
                  "root_entities": [{"persistent_id": 10, "children": [child]},
                                    {"persistent_id": 20, "children": [child]}]}
        normalized = normalize_sketchup(legacy)
        ids = [obj["id"] for obj in normalized["objects"]]
        self.assertEqual(len(set(ids)), 4)

    def test_legacy_missing_identity_fails(self):
        with self.assertRaises(ManifestError):
            normalize_sketchup({"schema_version": "1.0", "source_path": "test.skp", "sketchup_version": "2025",
                                "root_entities": [{"name": "Anonymous"}]})

    def test_text_search_is_accent_insensitive(self):
        candidates = find_candidates(self.manifest, ["balcao"])["candidates"]
        self.assertEqual(candidates[0]["id"], "demo:balcao-1")

    def test_rotation_stays_envelope_no_fabrication_claim(self):
        obj = self.manifest["objects"][0]
        obj["world_bounds_m"] = {"min": [-1, -1, 0], "max": [1, 1, 1]}
        spec = create_spec(self.manifest, "Rotação", [obj["id"]])
        dimension = spec["items"][0]["dimensions"][0]
        self.assertEqual(dimension["values_m"], [2, 2, 1])
        self.assertEqual(dimension["measurement_type"], "world_axis_aligned_envelope")
        self.assertIn("não é cota de fabricação", dimension["label"])
        self.assertTrue(any("rotação" in pending for pending in spec["items"][0]["pending"]))

    def test_unknown_ids_and_parent_child_selection_fail(self):
        with self.assertRaises(ManifestError):
            create_spec(self.manifest, "Test", ["unknown"])
        parent = self.manifest["objects"][0]
        child = copy.deepcopy(parent)
        child.update(id="demo:child", parent_id=parent["id"])
        self.manifest["objects"].append(child)
        self.manifest["extraction"]["object_count"] = 2
        with self.assertRaises(ManifestError):
            create_spec(self.manifest, "Test", [parent["id"], child["id"]])

    def test_verified_equivalence_required_for_quantity(self):
        obj = self.manifest["objects"][0]
        obj["definition_id"] = "definition:1"
        obj["properties"].update(instance_identity_verified=True, instance_equivalence_key="scale1-no-mirror-material1")
        second = copy.deepcopy(obj)
        second["id"] = "demo:balcao-2"
        self.manifest["objects"].append(second)
        self.manifest["extraction"].update(status="complete", limitations=[], object_count=2)
        spec = create_spec(self.manifest, "Test", [obj["id"], second["id"]])
        self.assertEqual(len(spec["items"]), 1)
        self.assertEqual(spec["items"][0]["quantity"]["value"], 2)
        self.assertEqual(spec["items"][0]["quantity"]["scope"], "selected_model_instances")
        second["properties"]["instance_equivalence_key"] = "scale2-no-mirror-material1"
        split = create_spec(self.manifest, "Test", [obj["id"], second["id"]])
        self.assertEqual(len(split["items"]), 2)
        self.manifest["extraction"]["status"] = "partial"
        pending = create_spec(self.manifest, "Test", [obj["id"], second["id"]])
        self.assertTrue(all(item["quantity"]["value"] is None for item in pending["items"]))

    def test_json_rejects_nan(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"number": NaN}', encoding="utf-8")
            with self.assertRaises(ManifestError):
                read_json(path)

    def test_cli_runs_without_cad_software(self):
        command = [sys.executable, str(SKILL / "scripts/memorial_cli.py")]
        doctor = subprocess.run(command + ["doctor"], capture_output=True, text=True, check=True)
        self.assertFalse(json.loads(doctor.stdout)["sketchup_required"])
        validate = subprocess.run(command + ["validate", str(SKILL / "examples/manifest-demo.json")],
                                  capture_output=True, text=True, check=True)
        self.assertTrue(json.loads(validate.stdout)["valid"])
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "spec.json"
            subprocess.run(command + ["spec", str(SKILL / "examples/manifest-demo.json"), "--project", "Demo",
                           "--ids", "demo:balcao-1", "--output", str(out)], capture_output=True, text=True, check=True)
            self.assertEqual(read_json(out)["status"], "draft_requires_review")

    def test_doctor_finds_flat_and_nested_sketchup_installations(self):
        with tempfile.TemporaryDirectory() as folder:
            binaries = [Path(folder) / "SketchUp/SketchUp 2025/SketchUp.exe",
                        Path(folder) / "SketchUp/SketchUp 2026/SketchUp/SketchUp.exe"]
            for binary in binaries:
                binary.parent.mkdir(parents=True)
                binary.touch()
            with mock.patch.dict("os.environ", {"ProgramFiles": folder}), mock.patch("shutil.which", return_value=None):
                paths = doctor()["applications"]["sketchup"]["paths"]
            for binary in binaries:
                self.assertIn(str(binary.resolve()), paths)

    def test_write_json_does_not_overwrite_or_create_invalid_output(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "existing.json"
            original = b'{"preserve": true}\n'
            target.write_bytes(original)
            with self.assertRaises(FileExistsError):
                write_json(target, {"replace": True})
            self.assertEqual(target.read_bytes(), original)
            invalid = Path(folder) / "invalid.json"
            with self.assertRaises(ValueError):
                write_json(invalid, {"bad": float("nan")})
            self.assertFalse(invalid.exists())

    def test_cli_preserves_source_and_existing_output(self):
        command = [sys.executable, str(SKILL / "scripts/memorial_cli.py")]
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "manifest.json"
            write_json(source, self.manifest)
            source_bytes = source.read_bytes()
            existing = Path(folder) / "existing.json"
            existing.write_bytes(b'keep this output')
            for target in (source, existing):
                original = target.read_bytes()
                result = subprocess.run(command + ["spec", str(source), "--project", "Demo", "--ids",
                                        "demo:balcao-1", "--output", str(target)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(target.read_bytes(), original)
            self.assertEqual(source.read_bytes(), source_bytes)

    def test_rhino_adapter_output_matches_core_contract_with_api_double(self):
        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        adapter = load("contract_rhino", SKILL / "adapters/rhino/extract_rhino.py")
        with mock.patch.dict(sys.modules, {"extract_rhino": adapter}):
            fixture = load("contract_rhino_fixture", SKILL / "adapters/rhino/test_extract_rhino.py")
        leaf = fixture.Object("leaf")
        block = fixture.Block("parent", fixture.definition("def", [leaf]), fixture.Transform.Identity)
        doc, rhino = fixture.scene([block], scale=0.001)
        manifest = adapter.Extractor(doc, rhino).extract()
        self.assertEqual(validate_manifest(manifest), [])
        self.assertEqual(manifest["objects"][1]["world_bounds_m"]["max"], [0.001, 0.002, 0.003])

    def test_max_adapter_output_matches_core_contract_with_api_double(self):
        spec = importlib.util.spec_from_file_location("contract_max", SKILL / "adapters/3dsmax/export_manifest.py")
        adapter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(adapter)
        ns = SimpleNamespace
        root = ns(children=[])
        node = ns(handle=1, children=[], parent=root, name="Synthetic node", material=None,
                  isHiddenInVpt=False, isFrozen=False, renderable=True, modifiers=[], layer=ns(name="Test"))
        root.children = [node]
        runtime = ns(maxFileName="synthetic.max", maxFilePath="C:/synthetic", rootNode=root,
                     units=ns(SystemType="millimeters", SystemScale=1), sliderTime=ns(frame=0, ticks=0),
                     frameRate=30, maxVersion=lambda: [27000, 0, 0], undefined=None,
                     getHandleByAnim=lambda value: value.handle, superClassOf=lambda value: "GeometryClass",
                     classOf=lambda value: "Editable_Poly", isGroupHead=lambda value: False,
                     isGroupMember=lambda value: False, getUserPropBuffer=lambda value: "",
                     matrix3=lambda value: value, areNodesInstances=lambda first, second: first is second,
                     InstanceMgr=ns(GetInstances=lambda value, out: (1, [value])),
                     nodeGetBoundingBox=lambda value, transform: [ns(x=0, y=0, z=0), ns(x=1000, y=2000, z=3000)])
        manifest = adapter.extract_manifest(runtime, ns(byref=lambda value: value))
        self.assertEqual(validate_manifest(manifest), [])
        self.assertEqual(manifest["objects"][0]["world_bounds_m"]["max"], [1.0, 2.0, 3.0])


if __name__ == "__main__":
    unittest.main()
