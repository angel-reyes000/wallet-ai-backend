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

#[{"name": "algo", "value": 2000}]
@routerCategories.get("/getGraphicCategories")
def getGraphicCategories (month: str, year: str, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get total to categories.")

        user_id = dataUser["id"]

        query = ""
        values = {}
        if (len(month) > 0 and len(year) > 0):
            query = """
                SELECT c.category_name AS name, SUM(t.amount) AS value FROM transactions t
                INNER JOIN categories c ON c.category_name = t.category
                WHERE t.user_id = :user_id AND EXTRACT(YEAR FROM t.date) = :year AND EXTRACT(MONTH FROM date) = :month
                GROUP BY c.category_name;
            """
            values = {"user_id": user_id, "year": year, "month": month}
        elif (len(year) > 0):
            query = """
                SELECT c.category_name AS name, SUM(t.amount) AS value FROM transactions t
                INNER JOIN categories c ON c.category_name = t.category
                WHERE t.user_id = :user_id AND EXTRACT(YEAR FROM t.date) = :year
                GROUP BY c.category_name;
            """
            values = {"user_id": user_id, "year": year}
        elif (len(month) > 0):
            raise HTTPException(status_code=400, detail="Can not filter only to month.")
        else:
            query = """
                SELECT c.category_name AS name, SUM(t.amount) AS value FROM transactions t
                INNER JOIN categories c ON c.category_name = t.category
                WHERE t.user_id = :user_id
                GROUP BY c.category_name;
            """
            values = {"user_id": user_id}

        response = db.execute(text(query), values)

        data = response.mappings().all()

        #print("getTotalToCategory: ", data)

        return data 

    except Exception as e:
        print("Error in getTotalToCategory: ", str(e))
        return HTTPException(status_code=400, detail="Error to get total to categories.")
       