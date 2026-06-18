#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一衛 guide 手書きリライト batch 36（study-plan-working：例えば上限対応）。"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_rewrite_path = Path(__file__).resolve().parent / "rewrites" / "study-plan-working.py"
_spec = importlib.util.spec_from_file_location("eisei1shu_study_plan_working", _rewrite_path)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

REWRITES = _mod.REWRITES
