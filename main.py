import asyncio
import logging
import random
import secrets

from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    wait_event_process_until_shutdown_sec: int = 60


class EventType(str, Enum):
    LONG = "LONG"
    MID = "MID"
    SHORT = "SHORT"


class EventRequest(BaseModel):
    type: EventType


class Event(EventRequest):
    key: str
    submitted_at: datetime
    processed_at: datetime | None = None


_ongoing_events: dict[str, Event] = {}
_total_events: dict[str, Event] = {}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # Wait until ongoing events finished
    waited_time_sec = 0
    while waited_time_sec <= settings.wait_event_process_until_shutdown_sec:
        if len(_ongoing_events) == 0:
            break
        wait_sec = 1
        await asyncio.sleep(wait_sec)
        waited_time_sec += wait_sec
        logger.info(f"Wait until ongoing events finished... {waited_time_sec} sec")


app = FastAPI(lifespan=lifespan)
settings = Settings()
logger = logging.getLogger("uvicorn")


async def _run_event(e: Event, how_long: int):
    _ongoing_events[e.key] = e
    logger.info(f"[{e.key}] Processing event")
    await asyncio.sleep(how_long)
    e.processed_at = datetime.now()
    del _ongoing_events[e.key]
    logger.info(f"[{e.key}] Finished processing event")


@app.post("/events/submit")
async def submit_event(event: EventRequest, wait: bool = False) -> Event:
    # event_key should be unique
    event_key = secrets.token_hex(16)
    _total_events[event_key] = Event(
        key=event_key,
        type=event.type,
        submitted_at=datetime.now(),
    )
    logger.info(f"[{event_key}] Received event")

    task = None
    if event.type == EventType.LONG:
        how_long = random.randint(10, 30)
        task = asyncio.create_task(_run_event(_total_events[event_key], how_long))
    elif event.type == EventType.MID:
        how_long = random.randint(5, 10)
        task = asyncio.create_task(_run_event(_total_events[event_key], how_long))
    elif event.type == EventType.SHORT:
        how_long = random.randint(1, 5)
        task = asyncio.create_task(_run_event(_total_events[event_key], how_long))

    if wait and task is not None:
        await task
    return _total_events[event_key]


@app.get("/events")
async def list_events(ongoing_only: bool = False) -> list[Event]:
    if ongoing_only:
        return list(_ongoing_events.values())
    return list(_total_events.values())


@app.get("/heartbeat")
async def heartbeat():
    return {"message": "doki doki v2"}
