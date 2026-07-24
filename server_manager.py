from pathlib import Path

import os
import re
import shutil
import socket
import sqlite3
import subprocess

import requests

from dotenv import load_dotenv
from mcstatus import JavaServer

from database import (
    add_server,
    get_all_server_ports,
    get_server_by_id,
    get_server_by_name,
    get_servers_by_user,
    init_database,
    remove_server
)


load_dotenv()


SERVER_HOST = os.getenv(
    "SERVER_HOST",
    "127.0.0.1"
)


SERVERS_DIRECTORY = Path(
    "/home/artur/minecraft-servers"
)

SERVER_NAME_PATTERN = re.compile(
    r"^[A-Za-z0-9_-]{3,32}$"
)

running_servers = {}


init_database()


def is_port_free(port: int):
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    ) as sock:
        result = sock.connect_ex(
            ("127.0.0.1", port)
        )

        return result != 0


def find_free_port():
    used_ports = set(
        get_all_server_ports()
    )

    port = 25565

    while (
        port in used_ports
        or not is_port_free(port)
    ):
        port += 1

    return port


def get_server(
    server_id: int,
    user_id: int
):
    return get_server_by_id(
        server_id,
        user_id
    )


def get_public_server_data(server: dict):
    return {
        "id": server["id"],
        "name": server["name"],
        "version": server["version"],
        "host": SERVER_HOST,
        "port": server["port"],
        "address": (
            f"{SERVER_HOST}:{server['port']}"
        ),
        "created_at": server["created_at"]
    }

def get_all_servers(user_id: int):
    servers = get_servers_by_user(
        user_id
    )

    return [
        get_public_server_data(server)
        for server in servers
    ]


def create_server(
    user_id: int,
    server_name: str,
    minecraft_version: str
):
    if not SERVER_NAME_PATTERN.fullmatch(
        server_name
    ):
        return {
            "success": False,
            "message": "Invalid server name"
        }

    existing_server = get_server_by_name(
        server_name,
        user_id
    )

    if existing_server is not None:
        return {
            "success": False,
            "message": (
                "A server with this name "
                "already exists"
            )
        }

    port = find_free_port()

    user_directory = (
        SERVERS_DIRECTORY
        / f"user-{user_id}"
    )

    server_path = (
        user_directory
        / server_name
    )

    if server_path.exists():
        return {
            "success": False,
            "message": (
                "The server directory "
                "already exists"
            )
        }

    try:
        server_path.mkdir(
            parents=True,
            exist_ok=False
        )

        download_server_jar(
            minecraft_version,
            server_path
        )

        properties = (
            f"server-port={port}\n"
            f"motd={server_name}\n"
        )

        with open(
            server_path / "server.properties",
            "w",
            encoding="utf-8"
        ) as file:
            file.write(properties)

        with open(
            server_path / "eula.txt",
            "w",
            encoding="utf-8"
        ) as file:
            file.write("eula=true\n")

        server_id = add_server(
            user_id=user_id,
            name=server_name,
            version=minecraft_version,
            port=port,
            path=str(server_path)
        )

    except sqlite3.IntegrityError:
        if server_path.exists():
            shutil.rmtree(server_path)

        return {
            "success": False,
            "message": (
                "The server name or port "
                "is already in use"
            )
        }

    except Exception as error:
        if server_path.exists():
            shutil.rmtree(server_path)

        return {
            "success": False,
            "message": (
                f"Server creation error: {error}"
            )
        }

    return {
        "success": True,
        "message": "Server successfully created",
        "server": {
            "id": server_id,
            "name": server_name,
            "version": minecraft_version,
            "port": port
        }
    }


def clean_running_server(server_id: int):
    entry = running_servers.pop(
        server_id,
        None
    )

    if entry is None:
        return

    log_file = entry.get("log_file")

    if (
        log_file is not None
        and not log_file.closed
    ):
        log_file.close()


def start_server(
    server_id: int,
    user_id: int
):
    server = get_server(
        server_id,
        user_id
    )

    if server is None:
        return {
            "success": False,
            "message": "Server not found"
        }

    existing_entry = running_servers.get(
        server_id
    )

    if existing_entry is not None:
        process = existing_entry["process"]

        if process.poll() is None:
            return {
                "success": False,
                "message": "Server is already running"
            }

        clean_running_server(server_id)

    if not is_port_free(server["port"]):
        return {
            "success": False,
            "message": "Server port is already in use"
        }

    server_path = Path(
        server["path"]
    )

    server_jar = (
        server_path
        / "server.jar"
    )

    if not server_jar.exists():
        return {
            "success": False,
            "message": "server.jar not found"
        }

    command = [
        "java",
        "-Xms2G",
        "-Xmx4G",
        "-jar",
        "server.jar",
        "nogui"
    ]

    log_file = open(
        server_path / "console.log",
        "a",
        encoding="utf-8"
    )

    try:
        process = subprocess.Popen(
            command,
            cwd=server_path,
            stdin=subprocess.PIPE,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True
        )

    except Exception:
        log_file.close()
        raise

    running_servers[server_id] = {
        "process": process,
        "log_file": log_file
    }

    return {
        "success": True,
        "message": "Server starting",
        "pid": process.pid
    }


def stop_server(
    server_id: int,
    user_id: int
):
    server = get_server(
        server_id,
        user_id
    )

    if server is None:
        return {
            "success": False,
            "message": "Server not found"
        }

    entry = running_servers.get(
        server_id
    )

    if entry is None:
        return {
            "success": False,
            "message": (
                "Server is not managed by "
                "this panel process"
            )
        }

    process = entry["process"]

    if process.poll() is not None:
        clean_running_server(server_id)

        return {
            "success": False,
            "message": "Server is offline"
        }

    try:
        if process.stdin is not None:
            process.stdin.write("stop\n")
            process.stdin.flush()

        process.wait(timeout=60)

    except subprocess.TimeoutExpired:
        process.terminate()

        try:
            process.wait(timeout=10)

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    finally:
        clean_running_server(server_id)

    return {
        "success": True,
        "message": "Server stopped"
    }


def send_command(
    server_id: int,
    user_id: int,
    command: str
):
    server = get_server(
        server_id,
        user_id
    )

    if server is None:
        return {
            "success": False,
            "message": "Server not found"
        }

    entry = running_servers.get(
        server_id
    )

    if entry is None:
        return {
            "success": False,
            "message": "Server is not running"
        }

    process = entry["process"]

    if process.poll() is not None:
        clean_running_server(server_id)

        return {
            "success": False,
            "message": "Server is offline"
        }

    if process.stdin is None:
        return {
            "success": False,
            "message": (
                "Server console is unavailable"
            )
        }

    process.stdin.write(
        command + "\n"
    )

    process.stdin.flush()

    return {
        "success": True,
        "message": (
            f"Command executed: {command}"
        )
    }


def get_server_status(
    server_id: int,
    user_id: int
):
    server = get_server(
        server_id,
        user_id
    )

    if server is None:
        return {
            "found": False,
            "online": False,
            "players": 0,
            "max_players": 0
        }

    try:
        address = (
            "127.0.0.1:"
            + str(server["port"])
        )

        minecraft_server = (
            JavaServer.lookup(address)
        )

        status = minecraft_server.status()

        return {
            "found": True,
            "online": True,
            "players": status.players.online,
            "max_players": status.players.max
        }

    except Exception:
        return {
            "found": True,
            "online": False,
            "players": 0,
            "max_players": 0
        }


def download_server_jar(
    minecraft_version: str,
    server_path: Path
):
    manifest_url = (
        "https://piston-meta.mojang.com/"
        "mc/game/version_manifest_v2.json"
    )

    response = requests.get(
        manifest_url,
        timeout=30
    )

    response.raise_for_status()

    manifest = response.json()
    version_data = None

    for version in manifest["versions"]:
        if version["id"] == minecraft_version:
            version_data = version
            break

    if version_data is None:
        raise ValueError(
            "Minecraft version "
            f"{minecraft_version} not found"
        )

    version_response = requests.get(
        version_data["url"],
        timeout=30
    )

    version_response.raise_for_status()

    version_info = (
        version_response.json()
    )

    server_download = (
        version_info["downloads"]
        ["server"]["url"]
    )

    server_jar_path = (
        server_path
        / "server.jar"
    )

    print(
        "Downloading Minecraft "
        f"{minecraft_version}..."
    )

    jar_response = requests.get(
        server_download,
        stream=True,
        timeout=60
    )

    jar_response.raise_for_status()

    with open(
        server_jar_path,
        "wb"
    ) as file:
        for chunk in jar_response.iter_content(
            chunk_size=1024 * 1024
        ):
            if chunk:
                file.write(chunk)

    return server_jar_path


def delete_server(
    server_id: int,
    user_id: int
):
    server = get_server(
        server_id,
        user_id
    )

    if server is None:
        return {
            "success": False,
            "message": "Server not found"
        }

    entry = running_servers.get(
        server_id
    )

    if (
        entry is not None
        and entry["process"].poll() is None
    ):
        return {
            "success": False,
            "message": "Stop the server first"
        }

    if entry is not None:
        clean_running_server(server_id)

    server_path = Path(
        server["path"]
    )

    try:
        if server_path.exists():
            shutil.rmtree(server_path)

    except OSError as error:
        return {
            "success": False,
            "message": (
                f"Could not delete server files: "
                f"{error}"
            )
        }

    deleted = remove_server(
        server_id,
        user_id
    )

    if not deleted:
        return {
            "success": False,
            "message": "Server not found"
        }

    return {
        "success": True,
        "message": "Server deleted"
    }