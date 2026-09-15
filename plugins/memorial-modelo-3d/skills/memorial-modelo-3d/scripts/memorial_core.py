"""Portable, evidence-preserving operations for memorial manifests.

All *_m coordinates and source.units are metres. unit_scale_to_m documents
the original API coordinate unit; it MUST NOT be applied to *_m values again.
No function in this module reads a proprietary model or opens a CAD application.
"""
from __future__ import annotations

import copy
import json
import math
import re
import unicodedata
from pathlib import Path


class ManifestError(ValueError):
    pass


def read_json(path):
    def invalid(value):
        raise ManifestError("Non-finite JSON number: " + value)
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=invalid)


def write_json(path, value):
    destination = Path(path)
    # Serialize before creating a destination, then use exclusive creation to
    # protect existing outputs (including symlinks) without a check/write race.
    rendered = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(rendered)


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def valid_bounds(value):
    return (isinstance(value, dict)
            and all(isinstance(value.get(k), list) and len(value[k]) == 3
                    and all(finite_number(n) for n in value[k]) for k in ("min", "max"))
            and all(a <= b and math.isfinite(b - a) for a, b in zip(value["min"], value["max"])))


def validate_manifest(data):
    """Return all detected errors. `complete` is an extraction claim, not QA approval.

    Complete requires object inventory, units, hierarchy and world bounds; rendered
    technical views remain separately capability-gated and reviewed by a person.
    """
    errors = []
    if not isinstance(data, dict):
        return ["Manifest must be a JSON object"]
    if data.get("schema_version") != "2.0":
        errors.append("schema_version must be '2.0'")
    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("source must be an object")
        source = {}
    for key in ("software", "version", "path"):
        if not isinstance(source.get(key), str) or not source[key].strip():
            errors.append("source.%s must be a nonempty string" % key)
    if source.get("units") != "m":
        errors.append("source.units must be 'm'; all normalized coordinates are metres")
    scale = source.get("unit_scale_to_m")
    if not finite_number(scale) or scale <= 0:
        errors.append("source.unit_scale_to_m must be finite and positive")
    for key in ("objects", "views", "materials", "warnings"):
        if not isinstance(data.get(key), list):
            errors.append(key + " must be an array")
    if isinstance(data.get("views"), list) and not all(isinstance(view, dict) for view in data["views"]):
        errors.append("views entries must be objects")
    objects = data.get("objects") if isinstance(data.get("objects"), list) else []
    extraction = data.get("extraction")
    if not isinstance(extraction, dict):
        errors.append("extraction must be an object")
        extraction = {}
    if extraction.get("status") not in ("complete", "partial"):
        errors.append("extraction.status must be complete or partial")
    for key in ("capabilities", "limitations"):
        values = extraction.get(key)
        if not isinstance(values, list) or not all(isinstance(v, str) and v for v in values):
            errors.append("extraction.%s must be an array of nonempty strings" % key)
    if "object_count" in extraction:
        count = extraction["object_count"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0 or count != len(objects):
            errors.append("extraction.object_count must match len(objects)")
    identifiers, parents = set(), {}
    for index, obj in enumerate(objects):
        prefix = "objects[%s]" % index
        if not isinstance(obj, dict):
            errors.append(prefix + " must be an object")
            continue
        identifier = obj.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(prefix + ".id must be a nonempty string")
        elif identifier in identifiers:
            errors.append(prefix + ".id duplicates " + identifier)
        else:
            identifiers.add(identifier)
            parents[identifier] = obj.get("parent_id")
        for key in ("name", "kind"):
            if not isinstance(obj.get(key), str) or (key == "kind" and not obj[key]):
                errors.append(prefix + "." + key + " must be a string")
        for key in ("parent_id", "definition_id", "layer"):
            if key not in obj or (obj[key] is not None and not isinstance(obj[key], str)):
                errors.append(prefix + "." + key + " must be a string or null")
        if not isinstance(obj.get("visible"), bool):
            errors.append(prefix + ".visible must be boolean")
        if "world_bounds_m" not in obj:
            errors.append(prefix + ".world_bounds_m is required (use null when unavailable)")
        elif obj["world_bounds_m"] is not None and not valid_bounds(obj["world_bounds_m"]):
            errors.append(prefix + ".world_bounds_m has invalid, non-finite or reversed bounds")
        if not isinstance(obj.get("materials"), list):
            errors.append(prefix + ".materials must be an array")
        if not isinstance(obj.get("properties"), dict):
            errors.append(prefix + ".properties must be an object")
    for identifier, parent in parents.items():
        if parent is not None and (not isinstance(parent, str) or parent not in identifiers):
            errors.append("%s has missing parent %r" % (identifier, parent))
        visited, cursor = set(), identifier
        while isinstance(cursor, str) and cursor in parents:
            if cursor in visited:
                errors.append("Hierarchy cycle involving " + identifier)
                break
            visited.add(cursor)
            cursor = parents[cursor]
    if extraction.get("status") == "complete":
        if extraction.get("limitations"):
            errors.append("Complete extraction cannot contain unresolved limitations")
        if any(isinstance(o, dict) and o.get("world_bounds_m") is None for o in objects):
            errors.append("Complete extraction cannot have unavailable world bounds")
        required = {"objects", "hierarchy", "world_bounds_m", "units"}
        capabilities = extraction.get("capabilities")
        if not isinstance(capabilities, list) or not all(isinstance(c, str) for c in capabilities) or not required.issubset(capabilities):
            errors.append("Complete extraction requires objects, hierarchy, world_bounds_m and units capabilities")
    # Metadata also must not hide NaN/Infinity, which JSON allows in some parsers.
    def scan(value, path):
        if isinstance(value, float) and not math.isfinite(value):
            errors.append(path + " contains a non-finite number")
        elif isinstance(value, dict):
            for key, child in value.items():
                scan(child, path + "." + str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                scan(child, "%s[%s]" % (path, index))
    scan(data, "manifest")
    return errors


def require_valid(data):
    errors = validate_manifest(data)
    if errors:
        raise ManifestError("\n".join(errors))
    return data


def normalize_sketchup(data):
    """Import the shipped v1 Ruby export conservatively, retaining original evidence.

    v1's nested world_bounds actually live in parent coordinates, and component
    definitions may be expanded once only. This importer never pretends the
    flattened result is a complete instance inventory or reconstructs missing data.
    """
    if not isinstance(data, dict) or data.get("schema_version") != "1.0" or not isinstance(data.get("root_entities"), list):
        raise ManifestError("Expected SketchUp bridge schema 1.0 with root_entities")
    if not data.get("source_path") or not data.get("sketchup_version"):
        raise ManifestError("Legacy manifest needs source_path and sketchup_version")
    definitions = {}
    for index, definition in enumerate(data.get("definitions", [])):
        for pid in definition.get("instance_persistent_ids", []):
            definitions.setdefault(str(pid), []).append((index, definition.get("name", "")))
    objects, warnings = [], []
    def walk(entities, parent_id=None, visible_ancestors=True):
        for index, entity in enumerate(entities):
            pid = entity.get("persistent_id")
            if pid is None:
                raise ManifestError("Legacy entity missing persistent_id; cannot make a traceable identity")
            identifier = ((parent_id + "/") if parent_id else "sketchup:") + str(pid)
            raw_bounds = entity.get("world_bounds", entity.get("bounds"))
            bounds = None
            if parent_id is None and isinstance(raw_bounds, dict):
                candidate = {"min": raw_bounds.get("min_m"), "max": raw_bounds.get("max_m")}
                if not valid_bounds(candidate):
                    raise ManifestError("Invalid legacy bounds for " + identifier)
                bounds = candidate
            elif raw_bounds is not None:
                warnings.append(identifier + ": nested v1 bounds are in parent space, not verified world coordinates")
            matches = definitions.get(str(pid), [])
            definition_id = "sketchup-definition:%s" % matches[0][0] if len(matches) == 1 else None
            visibility_known = isinstance(entity.get("visible"), bool)
            if not visibility_known:
                warnings.append(identifier + ": legacy visibility unavailable; excluded from visible scope pending verification")
            properties = {"source_persistent_id": str(pid), "legacy_path": entity.get("path", []),
                          "definition_name": entity.get("definition_name", ""),
                          "instance_identity_verified": False,
                          "visibility_verified": visibility_known,
                          "visibility_scope": "entity and ancestors; scene/tag visibility not evaluated"}
            for key in ("attributes", "local_dimensions_m", "transform", "children_omitted", "children_note", "locked"):
                if key in entity:
                    properties["legacy_" + key] = copy.deepcopy(entity[key])
            if parent_id is not None and raw_bounds is not None:
                properties["legacy_parent_space_bounds"] = copy.deepcopy(raw_bounds)
            material = entity.get("material")
            visible = visible_ancestors and entity.get("visible") is True and not entity.get("hidden", False)
            obj = {"id": identifier, "name": entity.get("name") or entity.get("definition_name") or "",
                   "kind": entity.get("type", "Unknown"), "parent_id": parent_id,
                   "definition_id": definition_id, "layer": entity.get("tag"),
                   "visible": bool(visible), "world_bounds_m": bounds,
                   "materials": [material] if material else [], "properties": properties}
            objects.append(obj)
            walk(entity.get("children", []), identifier, bool(visible))
    walk(data["root_entities"])
    normalized = {
        "schema_version": "2.0",
        "source": {"software": "sketchup", "version": str(data["sketchup_version"]),
                   "path": data["source_path"], "units": "m", "unit_scale_to_m": 0.0254,
                   "native_units": "inch (SketchUp Ruby API)", "legacy_display_units": data.get("model", {}).get("units", {})},
        "objects": objects, "views": copy.deepcopy(data.get("scenes", [])),
        "materials": copy.deepcopy(data.get("materials", [])), "warnings": warnings,
        "extraction": {"status": "partial", "object_count": len(objects),
                       "capabilities": ["objects", "hierarchy", "units", "legacy_scenes"],
                       "limitations": ["Legacy exporter may truncate depth and expand repeated definitions only once.",
                                       "Nested world bounds require re-extraction with accumulated transforms.",
                                       "Quantity and scene/layer visibility require native verification."]},
        "legacy_evidence": {key: copy.deepcopy(data[key]) for key in ("annotations", "definitions", "root_tag_summaries", "statistics") if key in data}
    }
    return require_valid(normalized)


def normalized_text(value):
    value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def find_candidates(data, terms, limit=30):
    require_valid(data)
    if not terms or not any(normalized_text(term) for term in terms):
        raise ManifestError("At least one nonempty search term is required")
    if limit < 1:
        raise ManifestError("limit must be positive")
    result = []
    for obj in data["objects"]:
        text = normalized_text(" ".join(str(obj.get(key) or "") for key in ("name", "layer", "kind")) + " " +
                               str(obj["properties"].get("definition_name", "")))
        matched = [term for term in terms if normalized_text(term) and normalized_text(term) in text]
        if matched:
            result.append({"id": obj["id"], "name": obj["name"], "layer": obj["layer"],
                           "visible": obj["visible"], "matched": matched, "score": 2 * len(matched)})
    return {"terms": terms, "candidates": sorted(result, key=lambda c: (-c["score"], c["id"]))[:limit],
            "notice": "Text matches are candidates; validate item identity and scope before documenting."}


def create_spec(data, project, object_ids, revision=""):
    require_valid(data)
    if not project.strip() or not object_ids:
        raise ManifestError("project and at least one selected object id are required")
    index = {obj["id"]: obj for obj in data["objects"]}
    if len(set(object_ids)) != len(object_ids):
        raise ManifestError("Selected object ids contain duplicates")
    unknown = sorted(set(object_ids) - index.keys())
    if unknown:
        raise ManifestError("Unknown selected object ids: " + ", ".join(unknown))
    selected = set(object_ids)
    for identifier in object_ids:
        parent = index[identifier]["parent_id"]
        while parent is not None:
            if parent in selected:
                raise ManifestError("Select parent or child separately to avoid double-counting: " + identifier)
            parent = index[parent]["parent_id"]
    items, used = [], set()
    for identifier in object_ids:
        if identifier in used:
            continue
        obj = index[identifier]
        group = [obj]
        # An adapter must explicitly verify native instance identity AND a
        # fabrication-equivalence signature (scale, handedness, material overrides).
        # Names or matching axis-aligned dimensions cannot prove equivalence.
        props = obj["properties"]
        signature = props.get("instance_equivalence_key")
        count_verified = (data["extraction"]["status"] == "complete" and obj["definition_id"] is not None
                          and props.get("instance_identity_verified") is True and isinstance(signature, str)
                          and bool(signature) and obj["visible"])
        if count_verified:
            group = [index[i] for i in object_ids if i not in used
                     and index[i]["definition_id"] == obj["definition_id"]
                     and index[i]["properties"].get("instance_identity_verified") is True
                     and index[i]["properties"].get("instance_equivalence_key") == signature
                     and index[i]["visible"]]
        used.update(member["id"] for member in group)
        dimensions, evidence = [], []
        bounds = obj["world_bounds_m"]
        if bounds is not None:
            spans = [hi - lo for lo, hi in zip(bounds["min"], bounds["max"])]
            dimensions.append({"label": "Envelope global X × Y × Z (não é cota de fabricação)",
                               "value": " × ".join(("%.2f" % n).replace(".", ",") for n in spans) + " m",
                               "source": "model", "measurement_type": "world_axis_aligned_envelope",
                               "values_m": spans, "object_id": identifier})
            evidence.append({"claim": "Envelope geométrico em eixos globais", "source": "model",
                             "locator": identifier + "/world_bounds_m"})
        pending = ["Confirmar recorte do item e conciliar com briefing e revisão vigente.",
                   "Obter e revisar vistas técnicas cotadas do item.",
                   "Confirmar cotas nominais, funcionais e de fabricação; envelope global pode variar com rotação.",
                   "Confirmar materiais, acabamentos, construção, instalação e interfaces."]
        if not bounds:
            pending.append("Envelope global indisponível; medir pelo adaptador nativo.")
        if not count_verified:
            pending.append("Quantidade produtiva a confirmar; identidade, equivalência ou inventário incompletos.")
        else:
            pending.append("Contagem de instâncias no recorte selecionado; conciliar quantidade de produção com o briefing.")
            evidence.append({"claim": "Instâncias equivalentes no recorte selecionado", "source": "model",
                             "locator": ", ".join(member["id"] for member in group)})
        if not obj["visible"]:
            pending.append("Objeto oculto: confirmar se pertence ao escopo de produção.")
        if data.get("synthetic") is True:
            pending.insert(0, "DEMONSTRAÇÃO SINTÉTICA — não representa modelo ou projeto real.")
        items.append({"number": "%02d" % (len(items) + 1), "title": obj["name"] or identifier,
                      "sheet_type": "detail", "plan_reference": [], "images": [],
                      "model_object_ids": [member["id"] for member in group], "dimensions": dimensions,
                      "quantity": {"value": len(group) if count_verified else None, "unit": "unidade",
                                   "source": "model" if count_verified else "pending", "scope": "selected_model_instances"},
                      "description": [], "production_classes": [], "construction": [], "materials_finishes": [],
                      "integrated_systems": [], "access_maintenance": [], "installation_notes": [],
                      "safety_notes": [], "pending": pending, "evidence": evidence})
    return {"schema_version": "2.0", "project": project, "revision": revision,
            "project_info": {"client": "", "location": "", "date": "", "units": "m"},
            "source_model": data["source"]["path"], "source_manifest_schema": "2.0",
            "status": "draft_requires_review", "synthetic": data.get("synthetic", False),
            "source_extraction": copy.deepcopy(data["extraction"]), "items": items}
