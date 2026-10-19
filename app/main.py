from fastapi import FastAPI
from app.routers.users import routerUsers
from app.routers.transactions import routerTransactions
from app.database.models import Base
from app.database.db import engine
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from app.routers.categories import routerCategories
from app.routers.types import routerTypes

load_dotenv()

url_frontend = os.getenv("FRONTEND_API")

def create_tables():
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables was created.")
    except Exception as e:
        print("Error in create_tables: ", str(e))
create_tables()

app = FastAPI()

origins = [str(url_frontend), ]

app.add_middleware(
    CORSMiddleware, 
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(routerUsers)

app.include_router(routerCategories)
app.include_router(routerTypes)

app.include_router(routerTransactions)