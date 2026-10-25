from fastapi import APIRouter, Depends, HTTPException
from app.routers.users import authUser
from app.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import Transaction
import calendar
from datetime import datetime

routerTransactions = APIRouter(prefix="/transactions", tags=["transaction"])

@routerTransactions.get("/getGraphicTransactions")
def getGraphicTransactions(month: str = None, year: str = None, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try: 

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]

        query = ""
        values = {}
        dataLabelX = None
        typeFilter = ""
        if (len(month) > 0 and len(year) > 0):
            query = """
                SELECT EXTRACT(DAY FROM date) AS day, SUM(amount) AS total FROM transactions
                WHERE user_id = :user_id AND EXTRACT(MONTH FROM date) = :month AND EXTRACT(YEAR FROM date) = :year
                GROUP BY EXTRACT(DAY FROM date);
            """
            values = {"user_id": user_id, "year": year, "month": month}
            dataLabelX = list(range(1, calendar.monthrange(int(year), int(month))[1] + 1))
            typeFilter = "month_year"
        elif (len(year) > 0):
            query = """
                SELECT TO_CHAR(date, 'month') AS month, SUM(amount) AS total FROM transactions
                WHERE user_id = :user_id AND EXTRACT(YEAR FROM date) = :year
                GROUP BY TO_CHAR(date, 'month');
            """
            values = {"user_id": user_id, "year": year}
            dataLabelX = list(calendar.month_name)[1:]
            typeFilter = "year"
        elif (len(month) > 0):
            raise HTTPException(status_code=400, detail="Can not filter only to month.")
        else:
            query = """
                SELECT EXTRACT(YEAR FROM date) AS year, SUM(amount) AS total FROM transactions
                WHERE user_id = :user_id AND EXTRACT(YEAR FROM date)::INTEGER BETWEEN EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER - 10 AND EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER
                GROUP BY EXTRACT(YEAR FROM date)
            """
            values = {"user_id": user_id}
            dataLabelX = [x for x in range(datetime.now().year - 9, datetime.now().year + 1 )]

        response = db.execute(text(query), values)

        data = response.mappings().all()

        listDataValues = [] 

        if typeFilter == "month_year":
            for v in dataLabelX:
                valuePass = False
                for d in data:
                    if d["day"] == v:
                        print("TOTAL", d["day"], v)
                        listDataValues.append(float(d["total"]))
                        valuePass = True
                if valuePass:
                    continue
                else:
                    listDataValues.append(0)
        elif typeFilter == "year":
            for v in dataLabelX:
                valuePass = False
                for d in data:          
                    if d["month"].lower().strip() == v.lower().strip():
                        listDataValues.append(int(d["total"]))
                        valuePass = True
                if valuePass:
                    continue
                else:
                    listDataValues.append(0)
        else:
            for v in dataLabelX:
                valuePass = False
                for d in data:   
                    if int(d["year"]) == int(v):
                        listDataValues.append(float(d["total"]))
                        valuePass = True
                if valuePass:
                    continue
                else:
                    listDataValues.append(0)
                    
        # print("LIST DATA:", listDataValues)
        # print(dataLabelX)

        # print(data)

        return [listDataValues, dataLabelX]

    except Exception as e:
        print("Error in getGraphicTransactions: ", str(e))
        return HTTPException(status_code=400, detail="Error to get filters.")

@routerTransactions.get("/getTotalBalancesExpensesIncomes")
def getTotalBalancesExpensesIncomes(month: str = None, year: str = None, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:
        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]
        
        query = ""
        if (len(month) > 0 and len(year) > 0):
            query = """
                SELECT SUM(amount) as total_balance, 
                    (SELECT SUM(amount) FROM transactions 
                        WHERE user_id = :user_id AND amount > 0 AND EXTRACT(YEAR FROM date) = :year AND EXTRACT(MONTH FROM date) = :month) AS total_incomes,
                    (SELECT SUM(amount) FROM transactions 
                        WHERE user_id = :user_id AND amount < 0 AND EXTRACT(YEAR FROM date) = :year AND EXTRACT(MONTH FROM date) = :month) AS total_expenses
                FROM transactions
                WHERE user_id = :user_id AND EXTRACT(YEAR FROM date) = :year AND EXTRACT(MONTH FROM date) = :month;
            """
            values = {"user_id": user_id, "year": year, "month": month}
        elif (len(year) > 0):
            query = """
                SELECT SUM(amount) as total_balance, 
                    (SELECT SUM(amount) FROM transactions 
                        WHERE user_id = :user_id AND amount > 0 AND EXTRACT(YEAR FROM date) = :year) AS total_incomes,
                    (SELECT SUM(amount) FROM transactions 
                        WHERE user_id = :user_id AND amount < 0 AND EXTRACT(YEAR FROM date) = :year) AS total_expenses
                FROM transactions
                WHERE user_id = :user_id AND EXTRACT(YEAR FROM date) = :year;
            """
            values = {"user_id": user_id, "year": year}
        elif (len(month) > 0):
            # query = """
            #     SELECT * FROM transactions
            #     WHERE user_id = :user_id AND EXTRACT(MONTH FROM date) = :month
            # """
            # values = {"user_id": user_id, "month": month}
            raise HTTPException(status_code=400, detail="Can not filter only to month.")
        else:
            query = """
                SELECT SUM(amount) as total_balance, 
                    (SELECT SUM(amount) FROM transactions WHERE user_id = :user_id AND amount > 0) AS total_incomes,
                    (SELECT SUM(amount) FROM transactions WHERE user_id = :user_id AND amount < 0) AS total_expenses
                FROM transactions
                WHERE user_id = :user_id;
            """
            values = {"user_id": user_id}

        response = db.execute(text(query), values)

        data = response.mappings().first()

        print(data)

        return data
        
    except Exception as e:
        print("Error in getTotalBalancesExpensesIncomes: ", str(e))
        return HTTPException(status_code=400, detail="Error to get filters.")

@routerTransactions.get("/getLastTransactions")
def getLastTransactions(month: str = None, year: str = None, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try: 

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]

        query = ""
        values = {}
        if (len(month) > 0 and len(year) > 0):
            query = """
                SELECT id, category, type, amount FROM transactions
                WHERE user_id = :user_id AND EXTRACT(YEAR FROM date) = :year AND EXTRACT(MONTH FROM date) = :month
                ORDER BY date ASC LIMIT 10;
            """
            values = {"user_id": user_id, "year": year, "month": month}
        elif (len(year) > 0):
            query = """
                SELECT id, category, type, amount FROM transactions
                WHERE user_id = :user_id AND EXTRACT(YEAR FROM date) = :year
                ORDER BY date ASC LIMIT 10;
            """
            values = {"user_id": user_id, "year": year}
        elif (len(month) > 0):
            raise HTTPException(status_code=400, detail="Can not filter only to month.")
        else:
            query = """
                SELECT id, category, type, amount FROM transactions
                WHERE user_id = :user_id
                ORDER BY date ASC LIMIT 10;
            """
            values = {"user_id": user_id}

        response = db.execute(text(query), values)

        data = response.mappings().all()
        #print(data)

        return data

    except Exception as e:
        print("Error in getGraphicTransactions: ", str(e))
        return HTTPException(status_code=400, detail="Error to get filters.")

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
        #print(data)

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

@routerTransactions.put("/updateTransaction")
def updateTransaction(transaction: Transaction, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to update data.")

        query = """
            UPDATE transactions 
            SET date = :date, description = :description, category = :category, type = :type, amount = :amount
            WHERE id = :id 
            RETURNING *;
        """

        values = {            
            "date": transaction.date,
            "description": transaction.description,
            "category": transaction.category,
            "type": transaction.type,
            "amount": transaction.amount,
            "id": transaction.id,
        }

        response = db.execute(text(query), values)
        db.commit()

        data = response.mappings().first()
        #print("UPDATE DATA: ", data)

        return data

    except Exception as e:
        print("Error in updateTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to update transaction.")
    
@routerTransactions.delete("/deleteTransaction")
def deleteTransaction (transaction_id: int, db: Session = Depends(get_db)):
    try:

        query = """
            DELETE FROM transactions 
            WHERE id = :id
            RETURNING *;
        """

        value = {"id": transaction_id}

        response = db.execute(text(query), value)
        db.commit()

        data = response.mappings().first()
        #print(data)

        return data

    except Exception as e:
        print("Error in deleteTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to delete transaction.")