from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.infrastructure.app_container import AppContainer
from src.infrastructure.db.database import SessionLocal
from fastapi import FastAPI

scheduler = AsyncIOScheduler()

async def daily_expiration_job():
    db = SessionLocal()
    try:
        stock_service = AppContainer.get_stock_service(db)
        await stock_service.check_expirations_and_notify()
    finally:
        db.close()


# Here you can add more scheduled jobs if needed, following the same pattern as above.





@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(daily_expiration_job, 'cron', hour=8, minute=0)
    # scheduler.add_job(daily_expiration_job, 'interval', minutes=1)
    
    # Here you can add more jobs to the scheduler if needed, following the same pattern as above.


    scheduler.start()
    print("⏰ Background scheduler started!")

    yield

    scheduler.shutdown()
    print("💤 Background scheduler stopped.")