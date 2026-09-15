"""Read the active 3ds Max scene through pymxs; never save or edit the model.

Initial adapter, awaiting validation in an installed 3ds Max 2021+ runtime.
Only standard-library Python and 3ds Max's bundled pymxs are required.
"""

import datetime
import json
import math
import os


SYSTEM_UNITS_TO_M = {
    "inches": 0.0254, "feet": 0.3048, "miles": 1609.344,
    "millimeters": 0.001, "centimeters": 0.01,
    "meters": 1.0, "kilometers": 1000.0,
}


def unit_scale_to_m(system_type, system_scale):
    """Use the SYSTEM unit, including its multiplier, never the display unit."""
    kind = str(system_type).lstrip("#").lower()
    if kind not in SYSTEM_UNITS_TO_M:
        raise ValueError("Unrecognized 3ds Max system unit: " + kind)
    value = float(system_scale) * SYSTEM_UNITS_TO_M[kind]
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Invalid system unit scale; extraction stopped.")
    return value


def _point(value, scale):
    result = [float(value.x) * scale, float(value.y) * scale,
              float(value.z) * scale]
    if not all(math.isfinite(item) for item in result):
        raise ValueError("Non-finite coordinate")
    return result


def _bounds(points, scale):
    minimum = _point(points[0], scale)
    maximum = _point(points[1], scale)
    if any(lo > hi for lo, hi in zip(minimum, maximum)):
        raise ValueError("Inverted bounding box")
    return {"min": minimum, "max": maximum}


def extract_manifest(rt=None, mxs=None):
    """Export current in-memory state; does not load a file or change frame."""
    if rt is None or mxs is None:
        try:
            import pymxs
        except ImportError as exc:
            raise RuntimeError("Run this adapter INSIDE 3ds Max with pymxs.") from exc
        rt = pymxs.runtime
        mxs = pymxs

    source_name = str(rt.maxFileName)
    if not source_name:
        raise RuntimeError("Open a saved .max working copy before extraction; this adapter never saves it.")
    source_path = os.path.join(str(rt.maxFilePath), source_name)
    scale = unit_scale_to_m(rt.units.SystemType, rt.units.SystemScale)
    frame = float(rt.sliderTime.frame)
    ticks = int(rt.sliderTime.ticks)
    warnings = []
    limitations = [
        "Initial adapter: native runtime validation is still required per Max version.",
        "Technical view images, isolated renders and dimension annotations are not exported.",
        "Bounds use the evaluated viewport node at the recorded frame, not render-only displacement.",
        "World axis-aligned bounds are envelopes, not necessarily fabrication dimensions.",
        "Material names are visual metadata and do not verify construction or finish specifications.",
        "User properties are preserved as raw text; arbitrary Custom Attributes are not traversed.",
        "External references, proxy contents and missing-plugin completeness are not verified.",
        "Instance relationships do not establish manufacturing quantity; groups and members overlap.",
        "Anim handles locate this scene snapshot; do not assume stable IDs after merge or reopening.",
    ]

    def read(label, getter, default=None):
        try:
            return getter()
        except Exception as exc:
            warnings.append("{}: {}: {}".format(label, type(exc).__name__, exc))
            return default

    def node_id(node):
        return "max-node-{}".format(int(rt.getHandleByAnim(node)))

    def walk_scene():
        # Keep hierarchy and include hidden/frozen nodes; never select/unhide them.
        pending = list(rt.rootNode.children)
        seen = set()
        result = []
        while pending:
            node = pending.pop()
            identifier = node_id(node)
            if identifier in seen:
                continue
            seen.add(identifier)
            result.append(node)
            pending.extend(list(node.children))
        return sorted(result, key=lambda node: int(rt.getHandleByAnim(node)))

    nodes = walk_scene()
    ids = {node_id(node) for node in nodes}
    definitions = {}
    materials = {}
    objects = []
    views = []

    def instance_definition(node):
        identifier = node_id(node)
        if identifier in definitions:
            return definitions[identifier]
        # InstanceMgr also returns linked BIM similarities. Filter those with the
        # exact native instance predicate before treating them as shared geometry.
        _, peers = rt.InstanceMgr.GetInstances(node, mxs.byref(None))
        instances = [peer for peer in peers if rt.areNodesInstances(node, peer)]
        handles = sorted({int(rt.getHandleByAnim(peer)) for peer in instances}
                         | {int(rt.getHandleByAnim(node))})
        definition = "max-definition-{}".format(handles[0])
        for handle in handles:
            definitions["max-node-{}".format(handle)] = definition
        return definition

    def material_tree(material):
        if material is None or material == rt.undefined:
            return []
        identifier = "max-material-{}".format(int(rt.getHandleByAnim(material)))
        if identifier in materials:
            return [identifier]
        record = {
            "id": identifier, "name": str(material.name),
            "class": str(rt.classOf(material)), "submaterials": [],
            "evidence": "model_material_label",
        }
        materials[identifier] = record
        # MAXScript submaterial APIs are one-based even through pymxs.
        count = int(rt.getNumSubMtls(material))
        for index in range(1, count + 1):
            child = rt.getSubMtl(material, index)
            record["submaterials"].extend(material_tree(child))
        return [identifier]

    for node in nodes:
        identifier = node_id(node)
        superclass = read(identifier + " superclass", lambda: str(rt.superClassOf(node)), "unknown")
        group_head = read(identifier + " group", lambda: bool(rt.isGroupHead(node)), False)
        kind = "group" if group_head else superclass.lower()
        kind = {"geometryclass": "geometry", "shape": "shape", "camera": "camera",
                "light": "light", "helper": "helper"}.get(kind, kind)
        parent = read(identifier + " parent", lambda: node.parent)
        parent_id = node_id(parent) if parent is not None and parent != rt.rootNode else None
        if parent_id not in ids:
            parent_id = None
        bounds = None
        if kind in ("geometry", "shape"):
            bounds = read(identifier + " world bounds",
                          lambda: _bounds(rt.nodeGetBoundingBox(node, rt.matrix3(1)), scale))
        visible = read(identifier + " visibility", lambda: not bool(node.isHiddenInVpt), False)
        properties = {
            "max_class": read(identifier + " class", lambda: str(rt.classOf(node))),
            "is_group_head": group_head,
            "is_group_member": read(identifier + " member", lambda: bool(rt.isGroupMember(node))),
            "is_frozen": read(identifier + " frozen", lambda: bool(node.isFrozen)),
            "renderable": read(identifier + " renderable", lambda: bool(node.renderable)),
            "user_property_buffer": read(identifier + " user properties", lambda: str(rt.getUserPropBuffer(node))),
            "modifiers": read(identifier + " modifiers", lambda: [str(rt.classOf(mod)) for mod in node.modifiers], []),
            "bounds_method": "nodeGetBoundingBox_identity_at_current_frame" if bounds else None,
            "visibility_semantics": "not isHiddenInVpt; occlusion and camera framing excluded",
        }
        objects.append({
            "id": identifier,
            "name": read(identifier + " name", lambda: str(node.name), identifier),
            "kind": kind, "parent_id": parent_id,
            "definition_id": read(identifier + " instances", lambda: instance_definition(node)),
            "layer": read(identifier + " layer", lambda: str(node.layer.name)),
            "visible": visible, "world_bounds_m": bounds,
            "materials": read(identifier + " materials", lambda: material_tree(node.material), []),
            "properties": properties,
        })
        if kind == "camera":
            # Metadata only: no active-viewport switch or camera creation.
            def camera_view():
                transform = node.transform
                return {
                    "id": "view-" + identifier, "name": str(node.name),
                    "kind": "camera", "object_id": identifier,
                    "position_m": _point(rt.getRow(transform, 4), scale),
                    "world_basis_rows": [_point(rt.getRow(transform, i), 1.0) for i in (1, 2, 3)],
                    "image_path": None, "frame": frame,
                }
            view = read(identifier + " camera", camera_view)
            if view:
                views.append(view)

    if int(rt.sliderTime.ticks) != ticks:
        raise RuntimeError("Frame changed during extraction; discard mixed-time result and retry.")
    return {
        "schema_version": "2.0",
        "source": {
            "software": "3dsmax", "version": str(rt.maxVersion()),
            "path": source_path, "units": "m", "unit_scale_to_m": scale,
            "system_unit_type": str(rt.units.SystemType),
            "system_unit_scale": float(rt.units.SystemScale),
            "state": "active_in_memory_document", "frame": frame, "ticks": ticks,
            "frame_rate": int(rt.frameRate),
        },
        "objects": objects, "views": views,
        "materials": sorted(materials.values(), key=lambda material: material["id"]),
        "warnings": warnings,
        "extraction": {
            "status": "partial",
            "adapter_version": "0.1.0", "native_runtime_validated": False,
            "extracted_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "object_count": len(objects),
            "capabilities": ["objects", "units", "hierarchy", "layers", "native_instance_relations",
                             "world_bounds_m", "material_labels", "camera_metadata",
                             "user_property_buffer", "current_frame", "viewport_visibility"],
            "limitations": limitations,
        },
    }


def export_manifest(output_path):
    """Write a NEW JSON file. Existing files and non-JSON destinations are rejected."""
    destination = os.path.abspath(os.fspath(output_path))
    if not destination.lower().endswith(".json"):
        raise ValueError("Choose a .json output; the model file is never an output.")
    if os.path.exists(destination):
        raise FileExistsError("Choose a new manifest filename: " + destination)
    data = extract_manifest()
    # Serialize before opening the file so invalid values cannot leave half a JSON.
    payload = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    with open(destination, "x", encoding="utf-8") as stream:
        stream.write(payload + "\n")
    print("Memorial: {} nodes exported to {} (partial; see limitations).".format(len(data["objects"]), destination))
    return data


def main():
    from pymxs import runtime as rt
    destination = rt.getSaveFileName(caption="Memorial 3D - new manifest JSON",
                                    types="JSON (*.json)|*.json|")
    if destination is None or destination == rt.undefined:
        print("Memorial: extraction cancelled.")
        return None
    return export_manifest(str(destination))


if __name__ == "__main__":
    main()
