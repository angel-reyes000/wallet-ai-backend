from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routers.users import routerUsers
from app.routers.transactions import routerTransactions
from app.database.db import engine
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from app.routers.categories import routerCategories
from app.routers.types import routerTypes
from app.routers.agent import routerAgent
from app.routers.cards import routerCards
from app.routers.settings import routerSettings

load_dotenv()

url_frontend = os.getenv("FRONTEND_API")

app = FastAPI()

origins = [str(url_frontend), ]

app.add_middleware(
    CORSMiddleware, 
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.exception_handler(RequestValidationError)
async def validation_error_handler (request: Request, exc: RequestValidationError):
    """Turns pydantic errors into {"detail": "<readable message>", "errors": [...]} (HTTP 422)."""
    errors = []

    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"] if part not in ("body", "query", "path", "header"))

        if err["type"] == "value_error":
            # raised by our own validators: the message is already written for the user
            message = str(err["msg"]).removeprefix("Value error, ")
        elif err["type"] == "missing":
            message = "Missing " + (field or "data") + "."
        else:
            message = "Invalid " + (field or "data") + ": " + str(err["msg"])

        if field == "authorization":
            message = "Missing authorization."

        errors.append({"field": field, "message": message})

    detail = errors[0]["message"] if errors else "Invalid data."

    return JSONResponse(status_code=422, content={"detail": detail, "errors": errors})

app.include_router(routerUsers)

app.include_router(routerCategories)
app.include_router(routerTypes)

app.include_router(routerTransactions)

app.include_router(routerAgent)

app.include_router(routerCards)

app.include_router(routerSettings)
