"""Launch with python.ExecuteFile <this file> clearUndoBuffer:false in 3ds Max."""
import os
import runpy

_memorial_namespace = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "export_manifest.py"))
_memorial_namespace["main"]()
