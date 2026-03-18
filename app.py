import sys, types, os

try:
    import pkg_resources
except ModuleNotFoundError:
    mod = types.ModuleType("pkg_resources")
    def _resource_filename(package, resource):
        import importlib.util
        spec = importlib.util.find_spec(package)
        if spec and spec.origin:
            return os.path.join(os.path.dirname(spec.origin), resource)
        return resource
    mod.resource_filename = _resource_filename
    mod.require = lambda s: []
    mod.working_set = []
    sys.modules["pkg_resources"] = mod

import streamlit as st

st.write("=== pykrx 파일 구조 확인 ===")

# pykrx 설치 경로 확인
import importlib.util
spec = importlib.util.find_spec("pykrx")
st.write(f"pykrx 경로: {spec.origin}")

import os
pykrx_dir = os.path.dirname(spec.origin)
for root, dirs, files in os.walk(pykrx_dir):
    level = root.replace(pykrx_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    st.write(f"{indent}{os.path.basename(root)}/")
    if level < 3:
        for f in files:
            st.write(f"{indent}  {f}")
