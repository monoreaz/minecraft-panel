from pathlib import Path
from mcstatus import JavaServer
import subprocess
# import json
import socket
import requests

from database import (
    init_database,
    add_server,
    get_server_by_name,
    get_all_servers as db_get_all_servers,
    remove_server
)

SERVERS_DIRECTORY = Path("/home/artur/minecraft-servers")
# DATABASE_FILE = Path("/home/artur/minecraft-panel/servers.json")

running_servers = {}

init_database()

# def load_servers():
#     with open(DATABASE_FILE, "r") as file:
#         return json.load(file)


# def save_servers(servers):
#     with open(DATABASE_FILE, "w") as file:
#         json.dump(servers, file, indent=4)


def is_port_free(port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        result = sock.connect_ex(("127.0.0.1", port))
        return result != 0


def find_free_port():

    servers = db_get_all_servers()
    used_ports = [
        server["port"]
        for server in servers
    ]

    port = 25565

    while (
        port in used_ports
        or not is_port_free(port)
    ):
        port += 1
    return port


# def get_server(server_name: str):
#     servers = load_servers()

#     for server in servers:
#         if server["name"] == server_name:
#             return server

#     return None


def get_server(server_name: str):

    return get_server_by_name(
        server_name
    )


def create_server(server_name: str, minecraft_version: str):
    # servers = load_servers()

    # for server in servers:
    if get_server(server_name) is not None:
        return {
            "success": False,
            "message":
            "A server with this name already exists"
        }

    port = find_free_port()

    server_path = SERVERS_DIRECTORY / server_name

    server_path.mkdir(parents=True)

    try:
        download_server_jar(minecraft_version, server_path)

        properties = (
            f"server-port={port}\n"
            f"motd={server_name}\n"
        )

        with open(server_path / "server.properties", "w") as file:
            file.write(properties)

        with open(server_path / "eula.txt", "w") as file:
            file.write("eula=true\n")

    except Exception as error:
        import shutil

        shutil.rmtree(server_path)

        return {
            "success": False,
            "message": f"Server creation error: {error}"
        }

    new_server = {
        "name": server_name,
        "version": minecraft_version,
        "port": port,
        "path": str(server_path)
    }

    # servers.append(new_server)
    # save_servers(servers)
    add_server(
        name=server_name,
        version=minecraft_version,
        port=port,
        path=str(server_path)
    )
    return {
        "success": True,
        "message": "Server successfully created",
        "server": new_server
    }


def get_all_servers():
    return db_get_all_servers()


def start_server(server_name: str):
    server = get_server(server_name)

    if server is None:
        return {
            "success": False,
            "message": "Server not found"
        }

    if server_name in running_servers:
        return {
            "success": False,
            "message": "Server is already running"
        }

    server_path = Path(server["path"])
    server_jar = server_path / "server.jar"

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

    process = subprocess.Popen(
        command,
        cwd=server_path,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    running_servers[server_name] = process

    return {
        "success": True,
        "message": "Server Online",
        "pid": process.pid
    }


def stop_server(server_name: str):
    if server_name not in running_servers:
        return {
            "success": False,
            "message": "Server is offline"
        }

    process = running_servers[server_name]

    process.stdin.write("stop\n")
    process.stdin.flush()

    process.wait()

    del running_servers[server_name]

    return {
        "success": True,
        "message": "Server stopped"
    }


def send_command(server_name: str, command: str):
    if server_name not in running_servers:
        return {
            "success": False,
            "message": "Server is not running"
        }

    process = running_servers[server_name]

    process.stdin.write(command + "\n")
    process.stdin.flush()

    return {
        "success": True,
        "message": f"Command executed: {command}"
    }


def get_server_status(server_name: str):
    server = get_server(server_name)

    if server is None:
        return {
            "online": False,
            "players": 0,
            "max_players": 0
        }

    try:
        address = "127.0.0.1:" + str(server["port"])

        minecraft_server = JavaServer.lookup(address)
        status = minecraft_server.status()

        return {
            "online": True,
            "players": status.players.online,
            "max_players": status.players.max
        }

    except Exception:
        return {
            "online": False,
            "players": 0,
            "max_players": 0
        }


def download_server_jar(minecraft_version: str, server_path: Path):
    manifest_url = (
        "https://piston-meta.mojang.com/"
        "mc/game/version_manifest_v2.json"
    )

    response = requests.get(manifest_url, timeout=30)
    response.raise_for_status()

    manifest = response.json()
    version_data = None

    for version in manifest["versions"]:
        if version["id"] == minecraft_version:
            version_data = version
            break

    if version_data is None:
        raise ValueError(
            f"Minecraft version {minecraft_version} not found"
        )

    version_response = requests.get(
        version_data["url"],
        timeout=30
    )

    version_response.raise_for_status()
    version_info = version_response.json()

    server_download = version_info["downloads"]["server"]["url"]

    server_jar_path = server_path / "server.jar"

    print(f"Downloading Minecraft {minecraft_version}...")

    jar_response = requests.get(
        server_download,
        stream=True,
        timeout=60
    )

    jar_response.raise_for_status()

    with open(server_jar_path, "wb") as file:
        for chunk in jar_response.iter_content(
            chunk_size=1024 * 1024
        ):
            if chunk:
                file.write(chunk)

    return server_jar_path


def delete_server(server_name: str):
    server = get_server(server_name)

    if server is None:
        return {
            "success": False,
            "message": "Server not found"
        }

    if server_name in running_servers:
        return {
            "success": False,
            "message": "Stop the server first"
        }

    server_path = Path(server["path"])

    if server_path.exists():
        import shutil

        shutil.rmtree(server_path)

    # servers = load_servers()
    remove_server(
        server_name
    )
    # servers = [
    #     server
    #     for server in servers
    #     if server["name"] != server_name
    # ]

    # save_servers(servers)

    return {
        "success": True,
        "message": "Server deleted"
    }