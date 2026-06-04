import docker
import random

client = docker.from_env()

IMAGE_NAME = "gnucash-xpra"


def get_free_port():
    return random.randint(15000, 25000)


def create_container(user_id):

    port = get_free_port()

    container = client.containers.run(
    	IMAGE_NAME,
    	detach=True,
    	network="gnucash-net",
    	name=f"gnucash-{user_id}-{port}",
	labels={
 	   "traefik.enable": "true",

 	   f"traefik.http.routers.gnucash-{port}.rule":
        	f"PathPrefix(`/session/{port}`)",

 	   f"traefik.http.routers.gnucash-{port}.entrypoints":
        	"web",

 	   f"traefik.http.routers.gnucash-{port}.middlewares":
        	f"slash-{port},strip-{port}",

 	   f"traefik.http.middlewares.slash-{port}.redirectregex.regex":
        	f"^(.*)/session/{port}$",

 	   f"traefik.http.middlewares.slash-{port}.redirectregex.replacement":
        	f"$1/session/{port}/",

 	   f"traefik.http.middlewares.strip-{port}.stripprefix.prefixes":
        	f"/session/{port}",

 	   f"traefik.http.services.gnucash-{port}.loadbalancer.server.port":
        	"14500",
	}
    )

    return {
        "container_id": container.id,
        "container_name": container.name,
        "internal_host": container.name,
    	"internal_port": 14500
    }


def stop_container(container_id):

    container = client.containers.get(container_id)

    container.stop()
