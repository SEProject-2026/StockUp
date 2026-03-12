from fastapi import FastAPI
from src.infrastructure.db.database import engine
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.db import models
from src.api.routes import auth_routes, management_routes, stock_routes
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.infrastructure.db.database import engine, SessionLocal
from src.infrastructure.app_container import AppContainer

scheduler = AsyncIOScheduler()

async def daily_expiration_job():
    db = SessionLocal()
    try:
        stock_service = AppContainer.get_stock_service(db)
        await stock_service.check_expirations_and_notify()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # ⚠️ הגדרה לבדיקה: מריץ את הפונקציה כל דקה! 
    scheduler.add_job(daily_expiration_job, 'cron', hour=8, minute=0)
    # scheduler.add_job(daily_expiration_job, 'interval', minutes=1)
    scheduler.start()
    print("⏰ Background scheduler started!")
    
    yield
    
    scheduler.shutdown()
    print("💤 Background scheduler stopped.")


models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="StockUp API", version="1.0.0", lifespan=lifespan)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)
app.include_router(auth_routes.router)
app.include_router(management_routes.router)
app.include_router(stock_routes.router)

@app.get("/")
def read_root():
    return {"message": "StockUp API is running and healthy! 🚀"}