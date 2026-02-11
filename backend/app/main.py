from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session
from app.routers.feeds import router as feeds_router
from app.routers.entries import router as entries_router
from app.routers.groups import router as groups_router
from app.routers.email_accounts import router as email_accounts_router
from app.utils.seed import seed_default_user
from app.tasks.scheduler import scheduler
from app.tasks.jobs import fetch_all_feeds, fetch_content_batch, sync_all_newsletters


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session() as session:
        await seed_default_user(session)
    scheduler.add_job(
        fetch_all_feeds,
        "interval",
        minutes=5,
        id="fetch_all_feeds",
        replace_existing=True,
    )
    scheduler.add_job(
        fetch_content_batch,
        "interval",
        minutes=10,
        id="fetch_content_batch",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_all_newsletters,
        "interval",
        minutes=15,
        id="sync_all_newsletters",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="RSS Reader API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(feeds_router)
app.include_router(entries_router)
app.include_router(groups_router)
app.include_router(email_accounts_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
