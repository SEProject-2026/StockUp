from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth_routes, management_routes, stock_routes, shopping_routes
from src.timed_alert_jobs import lifespan
from src.infrastructure.db.database import engine
from src.infrastructure.db import models

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
app.include_router(shopping_routes.router)

@app.get("/")
def read_root():
    return {"message": "StockUp API is running and healthy! 🚀"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)