# -*- coding: utf-8 -*-
"""Read the current Rhino document into manifest v2.0; never save the .3dm.

Run inside Rhino with _-RunPythonScript, or import and call export_current_doc.
Python 2.7/IronPython and Python 3 syntax; native Rhino 7/8 validation pending.
No third-party Python packages, SketchUp, or Blender required.
"""
from __future__ import print_function

import io
import json
import math
import os
import time

try:
    text_type = unicode
except NameError:
    text_type = str


def _text(value):
    return text_type(value) if value is not None else ""


def _xyz(value, scale=1.0):
    if hasattr(value, "IsValid") and not value.IsValid:
        raise ValueError("Rhino coordinate is unset or invalid")
    result = [float(value.X) * scale, float(value.Y) * scale,
              float(value.Z) * scale]
    if any(math.isnan(v) or math.isinf(v) for v in result):
        raise ValueError("Non-finite coordinate")
    return result


def _union_bounds(bounds):
    valid = [item for item in bounds if item is not None]
    if not valid:
        return None
    return {
        "min": [min(item["min"][axis] for item in valid) for axis in range(3)],
        "max": [max(item["max"][axis] for item in valid) for axis in range(3)],
    }


class Extractor(object):
    """No mutating Rhino API calls. Instances are expanded by occurrence path."""

    def __init__(self, doc, rhino, max_objects=200000, max_depth=64):
        self.doc = doc
        self.rhino = rhino
        self.max_objects = max_objects
        self.max_depth = max_depth
        self.objects = []
        self.materials = {}
        self.warnings = []
        self._warning_keys = set()
        self._layers_by_id = {}
        self._page_space_count = 0
        self._limit_reached = False
        self.scale = self._unit_scale()
        for layer in doc.Layers:
            if layer is not None and not layer.IsDeleted:
                self._layers_by_id[_text(layer.Id)] = layer

    def warn(self, code, message, object_id=None):
        # Limit diagnostic volume on damaged/very large models while retaining
        # the first actual occurrences. A truncation warning makes this explicit.
        key = (code, object_id, message)
        if key in self._warning_keys:
            return
        self._warning_keys.add(key)
        if len(self.warnings) >= 500:
            if len(self.warnings) == 500:
                self.warnings.append({"code": "warnings_truncated",
                                      "message": "More than 500 distinct warnings."})
            return
        row = {"code": code, "message": message}
        if object_id is not None:
            row["object_id"] = object_id
        self.warnings.append(row)

    def _unit_scale(self):
        units = self.doc.ModelUnitSystem
        # UnitScale may return a numerical result even for unitless data.
        # Do not silently turn unitless/custom-unit coordinates into metres.
        if _text(units).lower() in ("none", "unset", "customunits"):
            raise ValueError("The document must have a standard known unit system; "
                             "unitless/custom units need an explicit conversion first.")
        scale = float(self.rhino.RhinoMath.UnitScale(units, self.rhino.UnitSystem.Meters))
        if scale <= 0 or math.isnan(scale) or math.isinf(scale):
            raise ValueError("Cannot determine a valid document-to-metre unit scale.")
        return scale

    def _layer(self, obj, object_id):
        try:
            layer = self.doc.Layers[obj.Attributes.LayerIndex]
            if layer is None or layer.IsDeleted:
                raise ValueError("Layer is absent or deleted")
            return layer
        except Exception as exc:
            self.warn("layer_unavailable", _text(exc), object_id)
            return None

    def _visible(self, obj, layer, parent_visible):
        # This is model visibility, not a promise of visibility in every detail
        # viewport; per-viewport layer overrides are intentionally not evaluated.
        if not parent_visible or bool(obj.IsHidden):
            return False
        visited = set()
        while layer is not None:
            layer_id = _text(layer.Id)
            if layer_id in visited:
                self.warn("layer_cycle", "Layer hierarchy contains a cycle.")
                return False
            visited.add(layer_id)
            if not bool(layer.IsVisible):
                return False
            layer = self._layers_by_id.get(_text(layer.ParentLayerId))
        return True

    def _user_text(self, owner, object_id, source):
        try:
            values = owner.GetUserStrings()
            if values is None:
                return {}
            return {_text(key): _text(values[key]) for key in values.AllKeys if key is not None}
        except Exception as exc:
            self.warn("user_text_unavailable", source + ": " + _text(exc), object_id)
            return {}

    def _material_refs(self, obj, layer, parent_materials, object_id):
        try:
            source = obj.Attributes.MaterialSource
            enum = self.rhino.DocObjects.ObjectMaterialSource
            if source == enum.MaterialFromParent and parent_materials is not None:
                return list(parent_materials)
            if source == enum.MaterialFromObject:
                index = int(obj.Attributes.MaterialIndex)
            elif source in (enum.MaterialFromLayer, enum.MaterialFromParent):
                index = int(layer.RenderMaterialIndex) if layer is not None else -1
            else:
                self.warn("material_source_unsupported", _text(source), object_id)
                return []
            # -1 is Rhino's default material. Do not invent a production finish.
            if index < 0:
                return []
            material = self.doc.Materials[index]
            if material is None or material.IsDeleted:
                raise ValueError("Material entry is absent or deleted")
            material_id = "rhino-material:" + _text(material.Id)
            if material_id not in self.materials:
                color = material.DiffuseColor
                self.materials[material_id] = {
                    "id": material_id,
                    "name": _text(material.Name),
                    "properties": {
                        "rhino_material_index": index,
                        "diffuse_rgb": [int(color.R), int(color.G), int(color.B)],
                        "transparency": float(material.Transparency),
                        "evidence": "basic_model_material_not_manufacturing_specification",
                    },
                }
            return [material_id]
        except Exception as exc:
            self.warn("material_unavailable", _text(exc), object_id)
            return []

    def _geometry_bounds(self, obj, parent_transform, object_id):
        try:
            if obj.Geometry is None:
                raise ValueError("Object has no geometry")
            # This overload evaluates transformed geometry without modifying it;
            # transforming a precomputed AABB would overestimate rotated shapes.
            bounds = obj.Geometry.GetBoundingBox(parent_transform)
            if not bounds.IsValid:
                raise ValueError("Rhino returned an invalid or empty bounding box")
            return {"min": _xyz(bounds.Min, self.scale),
                    "max": _xyz(bounds.Max, self.scale)}
        except Exception as exc:
            self.warn("bounds_unavailable", _text(exc), object_id)
            return None

    def visit(self, obj, parent_transform, parent_id=None, path=None,
              parent_visible=True, parent_materials=None, definition_stack=()):
        if len(self.objects) >= self.max_objects:
            self._limit_reached = True
            self.warn("object_limit", "Extraction stopped at {0} occurrences.".format(self.max_objects))
            return None
        source_id = _text(obj.Id)
        path = list(path or []) + [source_id]
        object_id = "rhino:" + "/".join(path)
        layer = self._layer(obj, object_id)
        if layer is None:
            raise ValueError("Cannot determine visibility/material inheritance without the object's layer.")
        attrs = obj.Attributes
        is_instance = isinstance(obj, self.rhino.DocObjects.InstanceObject)
        visible = self._visible(obj, layer, parent_visible)
        materials = self._material_refs(obj, layer, parent_materials, object_id)
        row = {
            "id": object_id,
            "name": _text(attrs.Name),
            "kind": "block_instance" if is_instance else _text(obj.ObjectType).lower(),
            "parent_id": parent_id,
            "definition_id": None,
            "layer": _text(layer.FullPath) if layer is not None else None,
            "visible": visible,
            "world_bounds_m": None,
            "materials": materials,
            "properties": {
                "source_object_id": source_id,
                "instance_path": path,
                "rhino_object_type": _text(obj.ObjectType),
                "layer_id": _text(layer.Id) if layer is not None else None,
                "material_source": _text(attrs.MaterialSource),
                "is_reference": bool(obj.IsReference),
                "is_locked": bool(obj.IsLocked),
                "quantity_per_record": 1,
                "instance_identity_verified": False,
                "user_text": self._user_text(attrs, object_id, "attributes"),
                "geometry_user_text": self._user_text(obj.Geometry, object_id, "geometry"),
            },
        }
        self.objects.append(row)
        if not is_instance:
            row["world_bounds_m"] = self._geometry_bounds(obj, parent_transform, object_id)
            # Same source leaf can occur repeatedly inside placed blocks.
            if parent_id is not None:
                row["definition_id"] = "rhino-object:" + source_id
            return row["world_bounds_m"]
        try:
            definition = obj.InstanceDefinition
            if definition is None or definition.IsDeleted:
                raise ValueError("Block definition is unavailable")
            definition_id = _text(definition.Id)
            row["definition_id"] = "rhino-block:" + definition_id
            row["properties"]["definition_name"] = _text(definition.Name)
            row["properties"]["definition_user_text"] = self._user_text(
                definition, object_id, "block_definition")
            if not row["name"]:
                row["name"] = _text(definition.Name)
            if definition_id in definition_stack:
                self.warn("block_cycle", "Recursive block reference; descendants not expanded.", object_id)
                return None
            if len(definition_stack) >= self.max_depth:
                self.warn("block_depth_limit", "Nested block depth limit reached.", object_id)
                return None
            # Column-vector convention: ancestor transformation is on the left.
            transform = parent_transform * obj.InstanceXform
            children = definition.GetObjects()
            bounds = []
            complete = True
            for child in children:
                if self._limit_reached:
                    complete = False
                    break
                child_bounds = self.visit(child, transform, object_id, path, visible,
                                          materials, definition_stack + (definition_id,))
                bounds.append(child_bounds)
                if child_bounds is None:
                    complete = False
            if complete and bounds:
                row["world_bounds_m"] = _union_bounds(bounds)
            else:
                # A partial child union understates an assembly and cannot be
                # represented as its verified overall dimension.
                self.warn("block_bounds_incomplete", "Block bounds withheld because children are incomplete or empty.", object_id)
            return row["world_bounds_m"]
        except Exception as exc:
            self.warn("block_unavailable", _text(exc), object_id)
            return None

    def _named_views(self):
        result = []
        for index in range(self.doc.NamedViews.Count):
            try:
                view = self.doc.NamedViews[index]
                viewport = view.Viewport
                try:
                    target = _xyz(viewport.TargetPoint, self.scale)
                except (ValueError, AttributeError):
                    target = None
                    self.warn("named_view_target_unavailable", "Named view has no valid target point: " + _text(view.Name))
                result.append({
                    "id": "rhino-named-view:" + _text(index),
                    "name": _text(view.Name),
                    "kind": "camera_metadata",
                    "camera_location_m": _xyz(viewport.CameraLocation, self.scale),
                    "camera_direction": _xyz(viewport.CameraDirection),
                    "camera_up": _xyz(viewport.CameraUp),
                    "target_m": target,
                    "projection": "parallel" if viewport.IsParallelProjection else "perspective",
                    "image_path": None,
                })
            except Exception as exc:
                self.warn("named_view_unavailable", "View {0}: {1}".format(index, _text(exc)))
        return result

    def extract(self):
        settings = self.rhino.DocObjects.ObjectEnumeratorSettings()
        settings.NormalObjects = True
        settings.LockedObjects = True
        settings.HiddenObjects = True
        settings.ActiveObjects = True
        settings.ReferenceObjects = True
        settings.IdefObjects = False
        settings.DeletedObjects = False
        settings.IncludeLights = True
        identity = self.rhino.Geometry.Transform.Identity
        for obj in self.doc.Objects.GetObjectList(settings):
            if self._limit_reached:
                break
            if obj.IsInstanceDefinitionGeometry or obj.IsDeleted:
                continue
            if obj.Attributes.Space == self.rhino.DocObjects.ActiveSpace.PageSpace:
                self._page_space_count += 1
                continue
            try:
                self.visit(obj, identity)
            except Exception as exc:
                self.warn("object_unavailable", _text(exc), "rhino:" + _text(obj.Id))
        if self._page_space_count:
            self.warn("page_space_excluded", "{0} layout objects excluded from model inventory.".format(self._page_space_count))
        self.warn("technical_images_not_implemented", "This adapter exports metadata only; native isolated/coted images are not implemented.")
        views = self._named_views()
        return {
            "schema_version": "2.0",
            "source": {
                "software": "rhino",
                "version": _text(self.rhino.RhinoApp.Version),
                "path": _text(self.doc.Path) or None,
                "units": "m",
                "original_units": _text(self.doc.ModelUnitSystem),
                "unit_scale_to_m": self.scale,
                "document_state": "current_in_memory_document",
                "document_modified": bool(self.doc.Modified),
            },
            "objects": self.objects,
            "views": views,
            "materials": sorted(self.materials.values(), key=lambda material: material["id"]),
            "warnings": self.warnings,
            "extraction": {
                "status": "partial",
                "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "capabilities": ["objects", "hierarchy", "world_bounds_m", "units", "nested_instance_paths",
                                 "layer_hierarchy", "basic_material_assignments", "user_text",
                                 "named_view_metadata"],
                "limitations": [
                    "Technical isolated images and dimensions are not implemented.",
                    "Native Rhino 7/8 results still require validation against a real model.",
                    "AABB extents are world-axis extents, not dimensions in an item's local axes.",
                    "Production item selection and quantities require grouping by intended assembly level.",
                    "Appearance is not proof of manufacturing material or finish.",
                    "Per-face/PBR/renderer-specific materials and texture assets are not extracted.",
                    "Visibility excludes per-detail viewport overrides and clipping-plane effects.",
                    "Layout-space objects and inactive/unplaced block definitions are excluded.",
                    "Proxies and plugin-specific geometry may be incomplete; inspect warnings.",
                ],
            },
        }


def export_current_doc(output_dir, filename="manifest.json", doc=None,
                       max_objects=200000, max_depth=64):
    """Return the output path; require a new JSON target and a native Rhino doc."""
    import Rhino
    import scriptcontext

    doc = doc if doc is not None else scriptcontext.doc
    if not isinstance(doc, Rhino.RhinoDoc):
        raise RuntimeError("Run this script in Rhino, with the intended .3dm document active.")
    if not _text(doc.Path).strip():
        raise ValueError("The active model has no source file path. Save a working copy yourself before extraction.")
    if not output_dir:
        raise ValueError("An explicit output directory is required.")
    if filename != os.path.basename(filename) or not filename.lower().endswith(".json"):
        raise ValueError("Output filename must be a JSON basename.")
    if int(max_objects) < 1 or not 1 <= int(max_depth) <= 128:
        raise ValueError("max_objects must be positive and max_depth must be 1..128.")
    output_dir = os.path.abspath(output_dir)
    target = os.path.join(output_dir, filename)
    if os.path.exists(target):
        raise IOError("Output already exists; choose a new output directory: " + target)
    manifest = Extractor(doc, Rhino, int(max_objects), int(max_depth)).extract()
    # Serialise before creating the output. NaN/Infinity are never valid evidence.
    payload = json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with io.open(descriptor, "w", encoding="utf-8", closefd=True) as stream:
        stream.write(text_type(payload))
        stream.write(u"\n")
    return target


def main():
    import rhinoscriptsyntax as rs

    output_dir = os.environ.get("MEMORIAL_OUTPUT_DIR")
    if not output_dir:
        output_dir = rs.BrowseForFolder(None, "Choose an output folder for the Rhino manifest")
    if not output_dir:
        print("Memorial extraction cancelled; no output written.")
        return
    print("Manifest written: " + export_current_doc(output_dir))


if __name__ == "__main__":
    main()
