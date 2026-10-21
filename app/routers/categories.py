from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from app.database.db import get_db
from sqlalchemy import text
from app.routers.users import authUser

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


@routerCategories.get("/getTotalToCategory")
def totalToCategory (dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get total to categories.")

        user_id = dataUser["id"]

        value = {"id": user_id}

        query = """
            SELECT c.category_name AS name, SUM(t.amount) AS value FROM transactions t
            INNER JOIN categories c ON c.category_name = t.category
            WHERE t.user_id = :id
            GROUP BY c.category_name;
        """

        response = db.execute(text(query), value)

        data = response.mappings().all()

        return data

    except Exception as e:
        print("Error in getTotalToCategory: ", str(e))
        return HTTPException(status_code=400, detail="Error to get total to categories.")
       