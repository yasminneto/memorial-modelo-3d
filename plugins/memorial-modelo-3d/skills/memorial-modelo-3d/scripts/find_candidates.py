#!/usr/bin/env python3
import argparse
import json
import re
import unicodedata
from pathlib import Path


def normalize(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.encode("ascii", "ignore").decode().lower()).split())


def flatten(entities):
    for entity in entities:
        yield entity
        yield from flatten(entity.get("children", []))


def score(text, terms):
    normalized = normalize(text)
    points = 0
    matched = []
    for term in terms:
        needle = normalize(term)
        if needle and needle in normalized:
            points += 5 if normalized == needle else 2
            matched.append(term)
    return points, matched


def main():
    parser = argparse.ArgumentParser(description="Find scenes and model entities matching requested items.")
    parser.add_argument("manifest")
    parser.add_argument("terms", nargs="+")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--output")
    args = parser.parse_args()
    data = json.loads(Path(args.manifest).read_text(encoding="utf-8-sig"))
    candidates = []
    for scene in data.get("scenes", []):
        haystack = " ".join([scene.get("name", ""), scene.get("description", "")])
        points, matched = score(haystack, args.terms)
        if points:
            candidates.append({"kind": "scene", "score": points, "matched": matched, "item": scene})
    for tag_summary in data.get("root_tag_summaries", []):
        materials = " ".join(tag_summary.get("material_face_counts", {}).keys())
        haystack = " ".join([tag_summary.get("tag", ""), materials])
        points, matched = score(haystack, args.terms)
        if points:
            candidates.append({"kind": "tag", "score": points, "matched": matched, "item": tag_summary})
    for entity in flatten(data.get("root_entities", [])):
        haystack = " ".join([entity.get("name", ""), entity.get("definition_name", ""), entity.get("tag", ""), " ".join(entity.get("path", []))])
        points, matched = score(haystack, args.terms)
        if points:
            candidates.append({"kind": "entity", "score": points, "matched": matched, "item": entity})
    candidates.sort(key=lambda value: (-value["score"], value["kind"], str(value["item"].get("name", ""))))
    result = {"terms": args.terms, "candidates": candidates[: args.limit]}
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
