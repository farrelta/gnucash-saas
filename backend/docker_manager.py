"""
Docker container lifecycle manager.

Wraps the Docker SDK to create, stop, and remove per-user GnuCash
containers with Traefik service-discovery labels and persistent volume
mounts.
"""

import logging
import os
import random
from pathlib import Path
from typing import Optional

import docker
from docker.errors import NotFound

logger = logging.getLogger(__name__)

client = docker.from_env()

IMAGE_NAME: str = os.getenv("GNUCASH_IMAGE", "gnucash-xpra")
USER_DATA_PATH: str = os.getenv("USER_DATA_PATH", "/opt/gnucash-data")





def create_container(user_id: int, session_token: str) -> dict:
    """Spin up a new GnuCash container for *user_id*.

    - Creates a host directory for persistent user data.
    - Attaches the container to ``gnucash-net`` with Traefik labels so
      the reverse-proxy can discover it automatically via the session token.

    Returns a dict with ``container_id``, ``container_name``,
    ``internal_host``, and ``internal_port``.
    """
    # Ensure the user's persistent data directory exists
    user_dir = Path(USER_DATA_PATH) / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    container_name = f"gnucash-{session_token}"

    container = client.containers.run(
        IMAGE_NAME,
        detach=True,
        network="gnucash-net",
        name=container_name,
        volumes={
            str(user_dir): {
                "bind": "/data",
                "mode": "rw",
            }
        },
        labels={
            "traefik.enable": "true",
            # Router
            f"traefik.http.routers.gnucash-{session_token}.rule":
                f"PathPrefix(`/session/{session_token}`)",
            f"traefik.http.routers.gnucash-{session_token}.entrypoints":
                "websecure",
            f"traefik.http.routers.gnucash-{session_token}.middlewares":
                f"slash-{session_token},strip-{session_token}",
            # Middleware: trailing-slash redirect
            f"traefik.http.middlewares.slash-{session_token}.redirectregex.regex":
                f"^(.*)/session/{session_token}$",
            f"traefik.http.middlewares.slash-{session_token}.redirectregex.replacement":
                f"$1/session/{session_token}/",
            # Middleware: strip path prefix
            f"traefik.http.middlewares.strip-{session_token}.stripprefix.prefixes":
                f"/session/{session_token}",
            # Service port
            f"traefik.http.services.gnucash-{session_token}.loadbalancer.server.port":
                "14500",
        },
    )

    logger.info(
        "Created container %s (id=%s) for user %d",
        container_name,
        container.id,
        user_id,
    )

    return {
        "container_id": container.id,
        "container_name": container.name,
        "internal_host": container.name,
        "internal_port": 14500,
    }


def stop_container(container_id: str) -> None:
    """Stop a running container by *container_id*."""
    try:
        container = client.containers.get(container_id)
        container.stop()
        logger.info("Stopped container %s", container_id)
    except NotFound:
        logger.warning("Container %s not found — skipping stop", container_id)


def remove_container(container_id: str) -> None:
    """Stop and remove a container by *container_id*.

    Silently ignores containers that no longer exist.
    """
    try:
        container = client.containers.get(container_id)
        container.stop()
        container.remove()
        logger.info("Removed container %s", container_id)
    except NotFound:
        logger.warning(
            "Container %s not found — skipping removal", container_id
        )


def get_container_status(container_id: str) -> Optional[str]:
    """Return the Docker status string for *container_id*, or ``None``."""
    try:
        container = client.containers.get(container_id)
        return container.status
    except NotFound:
        return None
