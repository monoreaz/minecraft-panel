from database import get_all_servers


servers = get_all_servers()


for server in servers:

    print(server)