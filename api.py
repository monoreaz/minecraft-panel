from fastapi import FastAPI
from fastapi.responses import FileResponse

from auth import router as auth_router

from server_manager import (
    start_server,
    stop_server,
    send_command,
    get_server_status,
    create_server,
    get_all_servers,
    delete_server
)

app = FastAPI()

app.include_router(auth_router)

@app.get("/")
def home():
    return FileResponse("frontend/index.html")


@app.get("/create")
def create_page():
    return FileResponse("frontend/create.html")


@app.get("/servers")
def servers():
    return get_all_servers()


@app.post("/servers")
def create_new_server(name: str, version: str):
    return create_server(name, version)


@app.post("/servers/{server_name}/start")
def start_minecraft_server(server_name: str):
    return start_server(server_name)


@app.post("/servers/{server_name}/stop")
def stop_minecraft_server(server_name: str):
    return stop_server(server_name)


@app.post("/servers/{server_name}/day")
def set_day(server_name: str):
    return send_command(
        server_name,
        "time set day"
    )


@app.post("/servers/{server_name}/night")
def set_night(server_name: str):
    return send_command(
        server_name,
        "time set night"
    )


@app.get("/servers/{server_name}/status")
def server_status(server_name: str):
    return get_server_status(server_name)


@app.delete("/servers/{server_name}")
def delete_minecraft_server(server_name: str):
    return delete_server(server_name)