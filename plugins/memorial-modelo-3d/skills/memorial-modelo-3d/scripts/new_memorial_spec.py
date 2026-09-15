#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Create an auditable memorial specification template.")
    parser.add_argument("output")
    parser.add_argument("--project", required=True)
    parser.add_argument("--revision", default="")
    args = parser.parse_args()
    payload = {
        "schema_version": "2.0", "project": args.project, "revision": args.revision,
        "project_info": {"client": "", "location": "", "date": "", "units": ""},
        "source_model": "", "items": [{
            "number": "01", "title": "SUBSTITUIR", "sheet_type": "detail",
            "plan_reference": [],
            "images": [{"path": "", "caption": "Vista frontal cotada", "view": "front"}],
            "dimensions": [{"label": "L x P x A", "value": "", "source": "model"}],
            "quantity": {"value": 1, "unit": "unidade", "source": "pending"},
            "description": [], "production_classes": [], "construction": [],
            "materials_finishes": [], "integrated_systems": [],
            "access_maintenance": [], "installation_notes": [], "safety_notes": [],
            "pending": [], "evidence": [{"claim": "", "source": "model", "locator": ""}]
        }]
    }
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
