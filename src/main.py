from fastapi import FastAPI
from src.infrastructure.db.database import engine
from src.infrastructure.db import models
from src.api.routes import auth_routes, management_routes, stock_routes

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="StockUp API", version="1.0.0")


app.include_router(auth_routes.router)
app.include_router(management_routes.router)
app.include_router(stock_routes.router)

@app.get("/")
def read_root():
    return {"message": "StockUp API is running and healthy! 🚀"}