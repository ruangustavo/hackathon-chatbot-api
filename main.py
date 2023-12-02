from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.assistant import run_assistant
from app.websocket import ConnectionManager

app = FastAPI()
manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        await run_assistant(websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
