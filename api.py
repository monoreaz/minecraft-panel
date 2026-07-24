from typing import Annotated

from fastapi import (
    Depends,
    FastAPI
)

from fastapi.responses import FileResponse

from auth import (
    get_current_user,
    router as auth_router
)

from schemas import ServerCreate

from server_manager import (
    create_server,
    delete_server,
    get_all_servers,
    get_server_status,
    send_command,
    start_server,
    stop_server
)


app = FastAPI()

app.include_router(auth_router)


@app.get("/")
def home():
    return FileResponse(
        "frontend/index.html"
    )


@app.get("/create")
def create_page():
    return FileResponse(
        "frontend/create.html"
    )


@app.get("/servers")
def servers(
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return get_all_servers(
        current_user["id"]
    )


@app.post("/servers")
def create_new_server(
    data: ServerCreate,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return create_server(
        user_id=current_user["id"],
        server_name=data.name,
        minecraft_version=data.version
    )


@app.post(
    "/servers/{server_id}/start"
)
def start_minecraft_server(
    server_id: int,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return start_server(
        server_id,
        current_user["id"]
    )


@app.post(
    "/servers/{server_id}/stop"
)
def stop_minecraft_server(
    server_id: int,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return stop_server(
        server_id,
        current_user["id"]
    )


@app.post(
    "/servers/{server_id}/day"
)
def set_day(
    server_id: int,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return send_command(
        server_id,
        current_user["id"],
        "time set day"
    )


@app.post(
    "/servers/{server_id}/night"
)
def set_night(
    server_id: int,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return send_command(
        server_id,
        current_user["id"],
        "time set night"
    )


@app.get(
    "/servers/{server_id}/status"
)
def server_status(
    server_id: int,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return get_server_status(
        server_id,
        current_user["id"]
    )


@app.delete(
    "/servers/{server_id}"
)
def delete_minecraft_server(
    server_id: int,
    current_user: Annotated[
        dict,
        Depends(get_current_user)
    ]
):
    return delete_server(
        server_id,
        current_user["id"]
    )