import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.drivers.simulator import RigSimulator

ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
CONFIG_PATH = ROOT_DIR / "config.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

rig = RigSimulator(CONFIG)


async def simulation_loop():
    while True:
        rig.step(0.05)
        await asyncio.sleep(0.05)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(simulation_loop())
    yield
    task.cancel()


app = FastAPI(title="AMI Mic-Array Studio", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class TargetRequest(BaseModel):
    axis: str
    angle: float


class ToggleRequest(BaseModel):
    enabled: bool


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/api/target")
async def set_target(req: TargetRequest):
    ok = rig.set_target(req.axis, req.angle)
    return {"ok": ok, "angles": rig.get_telemetry()["angles"]}


@app.post("/api/estop")
async def set_estop(req: ToggleRequest):
    rig.set_estop(req.enabled)
    return {"ok": True, "estop": rig.estop_active}


@app.post("/api/park")
async def safe_park():
    rig.safe_park()
    return {"ok": True}


@app.post("/api/home")
async def home_all():
    rig.home_all()
    return {"ok": True}


@app.post("/api/motor-power")
async def motor_power(req: ToggleRequest):
    rig.set_motor_power(req.enabled)
    return {"ok": True, "motor_power": rig.motor_power}


@app.post("/api/ch10-mute")
async def ch10_mute(req: ToggleRequest):
    rig.set_ch10_mute(req.enabled)
    return {"ok": True, "ch10_muted": rig.ch10_muted}


@app.post("/api/transcribe")
async def run_transcription():
    if rig.transcribing:
        return {"ok": False, "msg": "Already transcribing"}
    rig.transcribing = True
    rig.add_log("STT", "Capturing audio from UMA-16 (Ch10 excluded) & running transcription...")

    async def finish_job():
        await asyncio.sleep(1.8)
        rig.transcribing = False
        rig.add_simulated_transcription()

    asyncio.create_task(finish_job())
    return {"ok": True}


@app.websocket("/ws")
async def telemetry_ws(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(rig.get_telemetry())
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        pass
