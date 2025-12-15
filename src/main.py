from fastapi import FastAPI

from src.api.routes import auth_routes 


app = FastAPI(title="StockUp API", version="1.0.0")


app.include_router(auth_routes.router)

@app.get("/")
def read_root():
    return {"message": "StockUp API is running and healthy! 🚀"}