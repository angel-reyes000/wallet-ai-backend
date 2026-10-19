from fastapi import APIRouter, Depends, HTTPException
from app.routers.users import authUser
from app.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import Transaction

routerTransactions = APIRouter(prefix="/transactions", tags=["transaction"])

@routerTransactions.get("/getTransactions")
def getTransactions (dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]

        query = "SELECT * FROM transactions WHERE user_id = :user_id"

        value = {"user_id": user_id}

        response = db.execute(text(query), value)

        data = response.mappings().all()
        print(data)

        return data

    except Exception as e:
        print("Error in getTransactions: ", str(e))
        return HTTPException(status_code=400, detail="Error to get transactions.")

@routerTransactions.post("/postTransaction")
def postTransaction (transaction: Transaction, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        if not transaction.date or not transaction.description or not transaction.category or not transaction.type or not transaction.amount:
            raise HTTPException(status_code=400, detail="Invalid or missing data.")

        user_id = dataUser["id"]

        query = """
            INSERT INTO transactions (date, description, category, type, amount, user_id)
            VALUES (:date, :description, :category, :type, :amount, :user_id)
            RETURNING *;
        """

        values = {
            "date": transaction.date,
            "description": transaction.description,
            "category": transaction.category,
            "type": transaction.type,
            "amount": transaction.amount,
            "user_id": user_id, 
        }

        response = db.execute(text(query), values)
        db.commit()

        data = response.mappings().first()
        print(data)

        return data

    except Exception as e:
        print("Error in postTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to create transaction.")