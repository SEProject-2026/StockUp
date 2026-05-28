from contextlib import asynccontextmanager
import subprocess
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.infrastructure.app_container import AppContainer
from src.infrastructure.db.database import AsyncSessionLocal
from fastapi import FastAPI

scheduler = AsyncIOScheduler()

async def daily_expiration_job():
    async with AsyncSessionLocal() as db:
        try:
            stock_service = AppContainer.get_stock_service(db)
            await stock_service.check_expirations_and_notify()
        finally:
            await db.close()

async def weekly_catalog_update_job():
    print("Starting Weekly Catalog Update...")
    try:
        subprocess.run(["python", "scraper.py"], check=True)
        subprocess.run(["python", "update_table.py"], check=True)
        print("✅ Weekly Catalog Update finished successfully!")
    except Exception as e:
        print(f"❌ Error during weekly update: {e}")

# Here you can add more scheduled jobs if needed, following the same pattern as above.

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(daily_expiration_job, 'cron', hour=8, minute=0)
    scheduler.add_job(weekly_catalog_update_job, 'cron', day_of_week='sun', hour=12, minute=0)

    # Here you can add more jobs to the scheduler if needed, following the same pattern as above.

    scheduler.start()
    print("⏰ Background scheduler started!")

    yield

    scheduler.shutdown()
    print("💤 Background scheduler stopped.")