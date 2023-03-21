import os
import logging
import asyncio
from logging.config import dictConfig

from lcu_driver import Connector
from lcu_driver.connection import Connection
from lcu_driver.events.managers import WebsocketEventResponse

from names import LCU


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[{asctime}][{levelname}] {filename}:{funcName}:{lineno} :: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

dictConfig(LOGGING)
logger = logging.getLogger(__name__)
connector = Connector()

seen_links: set[str] = set()


@connector.ready
async def connect(connection: Connection):
    logger.info("Connected")


def get_porofessor_link():
    lcu = LCU()
    link = lcu.get_porofessor_link()
    return link


def open_link(link: str):
    logger.info("opening link")
    os.popen(f'start "" "{link}"')


@connector.ws.register("/lol-lobby/")
async def lobby_handler(connection: Connection, event: WebsocketEventResponse):
    print("\n")
    logger.info(event.uri)


@connector.ws.register("/lol-champ-select/v1/session")
async def champ_select_session_handler(
    connection: Connection, event: WebsocketEventResponse
):
    print("\n")
    logger.info(event.uri)
    if not event.data:
        return
    game_id = event.data.get('gameId', None)

    await asyncio.sleep(3)
    if game_id and game_id not in seen_links:
        link = get_porofessor_link()
        seen_links.add(game_id)
        if link:
            open_link(link)


if __name__ == "__main__":
    connector.start()
