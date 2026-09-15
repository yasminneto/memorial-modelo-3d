#!/usr/bin/env python3
"""CLI for a portable memorial baseline; Python standard library only."""
import argparse
import glob
import json
import os
from pathlib import Path
import platform
import shutil
import sys

from memorial_core import (ManifestError, create_spec, find_candidates,
                           normalize_sketchup, read_json, validate_manifest, write_json)


def doctor():
    """Detect executables without launching applications or requiring SketchUp."""
    roots = list(dict.fromkeys(p for p in (os.environ.get("ProgramFiles"),
                 os.environ.get("ProgramFiles(x86)"), "C:/Program Files", "C:/Program Files (x86)") if p))
    patterns = {
        "sketchup": [str(Path(root) / suffix) for root in roots for suffix in
                    ("SketchUp/SketchUp */SketchUp.exe", "SketchUp/SketchUp */SketchUp/SketchUp.exe")] +
                    ["/Applications/SketchUp */SketchUp.app"],
        "rhino": [str(Path(root) / "Rhino */System/Rhino.exe") for root in roots] +
                 ["/Applications/Rhino *.app", "/Applications/Rhinoceros.app"],
        "3dsmax": [str(Path(root) / "Autodesk/3ds Max */3dsmax.exe") for root in roots],
    }
    applications = {}
    for name, probes in patterns.items():
        found = set()
        configured = os.environ.get("MEMORIAL_" + name.upper() + "_PATH")
        if configured and Path(configured).exists():
            found.add(str(Path(configured).resolve()))
        for probe in probes:
            found.update(str(Path(p).resolve()) for p in glob.glob(probe))
        for binary in {"sketchup": ["SketchUp.exe"], "rhino": ["Rhino.exe"], "3dsmax": ["3dsmax.exe"]}[name]:
            resolved = shutil.which(binary)
            if resolved:
                found.add(resolved)
        applications[name] = {"detected": bool(found), "paths": sorted(found),
                              "runtime_verified": False,
                              "note": "Executable presence only; version, license and extraction require native validation."}
    return {"platform": platform.platform(), "python": platform.python_version(),
            "core_ready": sys.version_info >= (3, 10), "applications": applications,
            "sketchup_required": False,
            "next_step": "Use the adapter for the source file, then validate its JSON manifest. Native application checks do not establish adapter compatibility."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Detect local applications; does not launch them")
    validate = commands.add_parser("validate", help="Validate a normalized v2 manifest")
    validate.add_argument("manifest")
    normalize = commands.add_parser("normalize-sketchup", help="Normalize a legacy SketchUp v1 manifest conservatively")
    normalize.add_argument("manifest")
    normalize.add_argument("--output", required=True)
    candidates = commands.add_parser("candidates", help="Find candidates by name, layer and definition")
    candidates.add_argument("manifest")
    candidates.add_argument("terms", nargs="+")
    candidates.add_argument("--limit", type=int, default=30)
    candidates.add_argument("--output")
    spec = commands.add_parser("spec", help="Create a draft technical spec from explicitly selected objects")
    spec.add_argument("manifest")
    spec.add_argument("--project", required=True)
    spec.add_argument("--revision", default="")
    spec.add_argument("--ids", nargs="+", required=True)
    spec.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor()
        else:
            data = read_json(args.manifest)
            if args.command == "validate":
                errors = validate_manifest(data)
                print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
                return 1 if errors else 0
            if args.command == "normalize-sketchup":
                result = normalize_sketchup(data)
            elif args.command == "candidates":
                result = find_candidates(data, args.terms, args.limit)
            else:
                result = create_spec(data, args.project, args.ids, args.revision)
        if getattr(args, "output", None):
            if Path(args.output).resolve() == Path(args.manifest).resolve():
                raise ManifestError("Output must not overwrite the source manifest")
            write_json(args.output, result)
            print(json.dumps({"output": str(Path(args.output).resolve())}, ensure_ascii=False))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ManifestError, OSError, ValueError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
