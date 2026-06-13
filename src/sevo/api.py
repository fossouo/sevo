"""Optional HTTP surface (FastAPI) mapping ``design/api_surface.json`` to the
in-process :class:`sevo.brain.Brain`.

This is a thin adapter: the brain is fully usable as a library (and the whole
test suite + experiment drive it directly, with no server). The HTTP layer
exists so a future deployment can expose the same nine endpoints over the
network. FastAPI is an *optional* dependency — import this module only if you
installed the ``[api]`` extra.

    pip install -e ".[api]"
    uvicorn sevo.api:app --reload
"""
from __future__ import annotations

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "The HTTP API needs the optional 'api' extra: pip install -e '.[api]'"
    ) from exc

from .brain import Brain
from .curriculum.cp_ce1_math import Problem

app = FastAPI(title="sevo — human brain API school", version="0.3.0")
_brain = Brain(seed=0)


class Percept(BaseModel):
    modality: str = "text"
    content: str
    source: str = "user"


class ConsolidateReq(BaseModel):
    mode: str = "sleep"
    advance_days: int = 1


@app.post("/perceive")
def perceive(p: Percept):
    return _brain.perceive(p.modality, p.content, p.source)


@app.post("/consolidate")
def consolidate(req: ConsolidateReq):
    return _brain.consolidate(mode=req.mode, advance_days=req.advance_days)


@app.get("/state/snapshot/latest")
def snapshot():
    return _brain.snapshot().__dict__


@app.get("/intelligence/profile")
def profile():
    s = _brain.snapshot()
    return s.cognitive_state["intelligence_profile"]
