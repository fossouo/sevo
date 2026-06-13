"""Runtime HTTP API (FastAPI) — the CP-appris brain as a persistent microservice.

A thin adapter over :class:`sevo.runtime.BrainService` (all logic and tests live
there, framework-agnostic). FastAPI is an *optional* dependency.

    pip install -e ".[api]"
    uvicorn sevo.api:app --reload

Endpoints (teacher channel vs assessment oracle kept strictly separate):

    POST /perceive      stimulus in
    POST /act           read-only response (no learning)
    POST /feedback      Emma's structured feedback -> the brain learns
    POST /consolidate   replay / "sleep"
    POST /replay        re-run an Emma teaching session over a node
    GET  /state         export the full learned state (brain_after)
    GET  /diff          Brain-naïf -> Brain-appris diff (+ genuine-learning verdict)
    POST /evaluate      oracle on a node's held-out bank (independent of teaching)
    POST /save  /load   persist / restore a brain state by path
"""
from __future__ import annotations

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
except ImportError as exc:  # pragma: no cover - optional dependency
    raise ImportError(
        "The HTTP API needs the optional 'api' extra: pip install -e '.[api]'"
    ) from exc

from typing import Any, Optional

from .brain import StateSchemaError
from .curriculum.factory import TaskFactoryError
from .eval import ItemLeakageError
from .persistence import EnvelopeSchemaError
from .runtime import BrainService

app = FastAPI(title="sevo — runtime brain API", version="0.4.0")
service = BrainService(seed=0)


class Percept(BaseModel):
    modality: str = "text"
    content: str
    source: str = "api"


class ActReq(BaseModel):
    node_id: str
    content: Any


class FeedbackReq(BaseModel):
    node_id: str
    content: Any
    correct: Optional[bool] = None      # if omitted, Emma grades from ground truth


class ConsolidateReq(BaseModel):
    mode: str = "sleep"
    advance_days: int = 1


class ReplayReq(BaseModel):
    node_id: str
    session_size: int = 8
    sessions: int = 1


class EvaluateReq(BaseModel):
    node_id: str
    items: Optional[list] = None        # None -> the node's held-out bank


class PathReq(BaseModel):
    path: str


class AuditReq(BaseModel):
    node_id: str


def _guard(fn):
    try:
        return fn()
    except TaskFactoryError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ItemLeakageError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post("/perceive")
def perceive(p: Percept):
    return service.perceive(p.modality, p.content, p.source)


@app.post("/act")
def act(r: ActReq):
    return _guard(lambda: service.act(r.node_id, r.content))


@app.post("/feedback")
def feedback(r: FeedbackReq):
    return _guard(lambda: service.feedback(r.node_id, r.content, r.correct))


@app.post("/consolidate")
def consolidate(r: ConsolidateReq):
    return service.consolidate(mode=r.mode, advance_days=r.advance_days)


@app.post("/replay")
def replay(r: ReplayReq):
    return _guard(lambda: service.replay_emma_session(r.node_id, r.session_size, r.sessions))


@app.get("/state")
def state():
    return service.state()


@app.get("/diff")
def diff():
    return {"diff": service.diff(), "genuine_learning": service.genuine_learning()}


@app.post("/evaluate")
def evaluate(r: EvaluateReq):
    return _guard(lambda: service.evaluate(r.node_id, r.items))


@app.get("/health")
def health():
    return service.health()


@app.get("/metrics")
def metrics():
    return service.metrics()


@app.post("/audit")
def audit(r: AuditReq):
    return _guard(lambda: service.audit(r.node_id))


@app.post("/session/start")
def session_start():
    return {"session_id": service.start_session()}


@app.get("/session/{session_id}")
def session_get(session_id: str):
    try:
        return service.get_session(session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"no session {session_id}") from e


@app.post("/session/{session_id}/replay")
def session_replay(session_id: str):
    try:
        return service.replay_session(session_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"no session {session_id}") from e


@app.post("/save")
def save(r: PathReq):
    service.save(r.path)
    return {"saved": r.path}


@app.post("/load")
def load(r: PathReq):
    global service
    try:
        service = BrainService.load(r.path)
    except (StateSchemaError, EnvelopeSchemaError) as e:
        raise HTTPException(status_code=409, detail=str(e)) from e      # incompatible schema
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"loaded": r.path, "day": service.brain.day,
            "schema_version": service.brain.export_state()["schema_version"]}
