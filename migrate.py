from database import (
    init_database,
    add_server
)


init_database()


add_server(
    name="survivalol",
    version="1.21.1",
    port=25565,
    path="/home/artur/minecraft-servers/survivalol"
)


print("Server has been added to the database")