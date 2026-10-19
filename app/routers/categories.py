from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from app.database.db import get_db
from sqlalchemy import text

routerCategories = APIRouter(prefix="/categories")

@routerCategories.get("/getCategories")
def getCategories(db: Session = Depends(get_db)):
    try: 

        query = "SELECT * FROM categories"

        response = db.execute(text(query))

        data = response.mappings().all()

        return data

    except Exception as e:
        print("Error in getCategories: ", str(e))
        return HTTPException(status_code=400, detail="Error to get categories.")