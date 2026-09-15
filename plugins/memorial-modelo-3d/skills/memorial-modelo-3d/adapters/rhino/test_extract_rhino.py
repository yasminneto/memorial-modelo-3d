"""Algorithm tests with synthetic API doubles, NOT native Rhino validation."""
import itertools
import types
import unittest

import extract_rhino


def ns(**kwargs):
    return types.SimpleNamespace(**kwargs)


class Transform:
    def __init__(self, matrix=None):
        self.matrix = matrix or [[int(i == j) for j in range(4)] for i in range(4)]

    def __mul__(self, other):
        a, b = self.matrix, other.matrix
        return Transform([[sum(a[i][k] * b[k][j] for k in range(4))
                           for j in range(4)] for i in range(4)])

    def point(self, xyz):
        return [sum(self.matrix[i][j] * list(xyz + (1,))[j] for j in range(4)) for i in range(3)]


Transform.Identity = Transform()


def vector(xyz):
    return ns(X=xyz[0], Y=xyz[1], Z=xyz[2], IsValid=True)


class Geometry:
    def __init__(self, valid=True):
        self.valid = valid

    def GetUserStrings(self):
        return None

    def GetBoundingBox(self, transform):
        points = [transform.point(p) for p in itertools.product((0, 1), (0, 2), (0, 3))]
        return ns(IsValid=self.valid,
                  Min=vector([min(p[i] for p in points) for i in range(3)]),
                  Max=vector([max(p[i] for p in points) for i in range(3)]))


class Object:
    def __init__(self, name, valid=True):
        self.Id = name
        self.Geometry = Geometry(valid)
        self.ObjectType = "Brep"
        self.IsReference = self.IsLocked = self.IsHidden = False
        self.IsDeleted = self.IsInstanceDefinitionGeometry = False
        self.Attributes = ns(Name=name, LayerIndex=0, MaterialSource="layer", MaterialIndex=-1,
                             Space="model", GetUserStrings=lambda: None)


class Block(Object):
    def __init__(self, name, definition, transform):
        super().__init__(name)
        self.InstanceDefinition = definition
        self.InstanceXform = transform
        self.ObjectType = "InstanceReference"


def definition(name, children):
    return ns(Id=name, Name=name, IsDeleted=False, GetObjects=lambda: children,
              GetUserStrings=lambda: None)


def scene(objects, scale=1.0):
    rhino = ns(
        RhinoMath=ns(UnitScale=lambda source, target: scale),
        UnitSystem=ns(Meters="Meters"), RhinoApp=ns(Version="synthetic-test"),
        Geometry=ns(Transform=Transform),
        DocObjects=ns(InstanceObject=Block, ObjectEnumeratorSettings=types.SimpleNamespace,
                      ObjectMaterialSource=ns(MaterialFromParent="parent", MaterialFromObject="object",
                                              MaterialFromLayer="layer"),
                      ActiveSpace=ns(PageSpace="page")))
    layer = ns(Id="layer0", FullPath="Items", IsDeleted=False, IsVisible=True,
               ParentLayerId="empty", RenderMaterialIndex=-1)
    doc = ns(ModelUnitSystem="Meters", Layers=[layer], Materials=[], Modified=False,
             NamedViews=ns(Count=0), Path="synthetic.3dm",
             Objects=ns(GetObjectList=lambda settings: objects))
    return doc, rhino


class ExtractionAlgorithmTests(unittest.TestCase):
    def test_nested_rotation_scale_and_distinct_occurrences(self):
        rotate = Transform([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        scale_translate = Transform([[2, 0, 0, 10], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        translate = Transform([[1, 0, 0, 20], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        inner = Block("inner", definition("leaf-def", [Object("leaf")]), rotate)
        outer = definition("assembly", [inner])
        doc, rhino = scene([Block("first", outer, scale_translate), Block("second", outer, translate)])
        result = extract_rhino.Extractor(doc, rhino).extract()
        rows = {item["id"]: item for item in result["objects"]}
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows["rhino:first/inner/leaf"]["world_bounds_m"],
                         {"min": [6., 0., 0.], "max": [10., 1., 3.]})
        self.assertEqual(rows["rhino:second/inner/leaf"]["world_bounds_m"],
                         {"min": [18., 0., 0.], "max": [20., 1., 3.]})
        self.assertEqual(rows["rhino:first"]["world_bounds_m"], rows["rhino:first/inner/leaf"]["world_bounds_m"])
        self.assertEqual(rows["rhino:first/inner/leaf"]["parent_id"], "rhino:first/inner")
        self.assertEqual(rows["rhino:first"]["definition_id"], rows["rhino:second"]["definition_id"])

    def test_scale_to_metres_and_hidden_ancestor(self):
        block = Block("parent", definition("def", [Object("leaf")]), Transform.Identity)
        block.IsHidden = True
        doc, rhino = scene([block], scale=0.001)
        rows = extract_rhino.Extractor(doc, rhino).extract()["objects"]
        self.assertFalse(rows[1]["visible"])
        self.assertEqual(rows[1]["world_bounds_m"]["max"], [0.001, 0.002, 0.003])

    def test_missing_child_bounds_never_understate_assembly(self):
        block = Block("assembly", definition("def", [Object("good"), Object("bad", valid=False)]), Transform.Identity)
        doc, rhino = scene([block])
        result = extract_rhino.Extractor(doc, rhino).extract()
        self.assertIsNone(result["objects"][0]["world_bounds_m"])
        self.assertIn("block_bounds_incomplete", [warning["code"] for warning in result["warnings"]])

    def test_recursive_definition_stops_and_marks_partial(self):
        children = []
        block = Block("cycle", definition("recursive", children), Transform.Identity)
        children.append(block)
        doc, rhino = scene([block])
        result = extract_rhino.Extractor(doc, rhino).extract()
        self.assertEqual(len(result["objects"]), 2)
        self.assertEqual(result["extraction"]["status"], "partial")
        self.assertIn("block_cycle", [warning["code"] for warning in result["warnings"]])

    def test_unitless_and_unset_points_are_rejected(self):
        doc, rhino = scene([])
        doc.ModelUnitSystem = "None"
        with self.assertRaises(ValueError):
            extract_rhino.Extractor(doc, rhino)
        with self.assertRaises(ValueError):
            extract_rhino._xyz(ns(X=-1e308, Y=-1e308, Z=-1e308, IsValid=False))


if __name__ == "__main__":
    unittest.main()
