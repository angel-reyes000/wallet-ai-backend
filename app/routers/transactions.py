from fastapi import APIRouter, Depends, HTTPException, Query
from app.routers.users import authUser
from app.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import Transaction
from app.validation import period_filters
import calendar
from datetime import datetime

routerTransactions = APIRouter(prefix="/transactions", tags=["transaction"])

@routerTransactions.get("/getGraphicTransactions")
def getGraphicTransactions(period = Depends(period_filters), dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try: 

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]
        month, year = period

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

    except HTTPException:
        raise

    except Exception as e:
        print("Error in getGraphicTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to get filters.")

@routerTransactions.get("/getTotalBalancesExpensesIncomes")
def getTotalBalancesExpensesIncomes(period = Depends(period_filters), dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:
        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]
        month, year = period
        
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
        
    except HTTPException:
        raise

    except Exception as e:
        print("Error in getTotalBalancesExpensesIncomes: ", str(e))
        raise HTTPException(status_code=400, detail="Error to get filters.")

@routerTransactions.get("/getLastTransactions")
def getLastTransactions(period = Depends(period_filters), dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try: 

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]
        month, year = period

        query = ""
        values = {}
        if (len(month) > 0 and len(year) > 0):
            query = """
                SELECT id, category, card, amount FROM transactions
                WHERE user_id = :user_id AND EXTRACT(YEAR FROM date) = :year AND EXTRACT(MONTH FROM date) = :month
                ORDER BY date DESC LIMIT 10;
            """
            values = {"user_id": user_id, "year": year, "month": month}
        elif (len(year) > 0):
            query = """
                SELECT id, category, card, amount FROM transactions
                WHERE user_id = :user_id AND EXTRACT(YEAR FROM date) = :year
                ORDER BY date DESC LIMIT 10;
            """
            values = {"user_id": user_id, "year": year}
        elif (len(month) > 0):
            raise HTTPException(status_code=400, detail="Can not filter only to month.")
        else:
            query = """
                SELECT id, category, card, amount FROM transactions
                WHERE user_id = :user_id
                ORDER BY date DESC LIMIT 10;
            """
            values = {"user_id": user_id}

        response = db.execute(text(query), values)

        data = response.mappings().all()
        #print(data)

        return data

    except HTTPException:
        raise

    except Exception as e:
        print("Error in getGraphicTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to get filters.")

@routerTransactions.get("/getTransactions")
def getTransactions (dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]

        query = """SELECT
                   t.id, 
                   t.date,
                   t.description,
                   t.category,
                   t.card, 
                   t.amount,
                   c.type
                   FROM transactions t 
                   LEFT JOIN cards c ON t.card = c.name
                   WHERE t.user_id = :user_id"""

        value = {"user_id": user_id}

        response = db.execute(text(query), value)

        data = response.mappings().all()
        print(data)

        return data

    except HTTPException:
        raise

    except Exception as e:
        print("Error in getTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to get transactions.")

def validateTransactionReferences (db: Session, user_id: int, transaction: Transaction):
    """The category must exist and the card must be 'Cash' or one of the user's own cards."""
    category = db.execute(
        text("SELECT 1 FROM categories WHERE category_name = :category"),
        {"category": transaction.category}
    ).first()

    if not category:
        raise HTTPException(status_code=400, detail="Invalid category.")

    if transaction.card != "Cash":
        card = db.execute(
            text("SELECT 1 FROM cards WHERE user_id = :user_id AND name = :card"),
            {"user_id": user_id, "card": transaction.card}
        ).first()

        if not card:
            raise HTTPException(status_code=400, detail="Invalid card.")

@routerTransactions.post("/postTransaction")
def postTransaction (transaction: Transaction, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to get data user.")

        user_id = dataUser["id"]

        # date, description, category, card and amount were already validated by the schema
        validateTransactionReferences(db, user_id, transaction)

        query = """
            INSERT INTO transactions (date, description, category, card, amount, user_id)
            VALUES (:date, :description, :category, :card, :amount, :user_id)
            RETURNING *;
        """

        values = {
            "date": transaction.date,
            "description": transaction.description,
            "category": transaction.category,
            "card": transaction.card,
            "amount": transaction.amount,
            "user_id": user_id,
        }

        response = db.execute(text(query), values)
        db.commit()

        data = response.mappings().first()
        print(data)

        return data

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        print("Error in postTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to create transaction.")

@routerTransactions.put("/updateTransaction")
def updateTransaction(transaction: Transaction, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to update data.")

        if not transaction.id:
            raise HTTPException(status_code=400, detail="Missing transaction id.")

        user_id = dataUser["id"]

        validateTransactionReferences(db, user_id, transaction)

        # user_id in the WHERE: a user can only edit their own transactions
        query = """
            UPDATE transactions
            SET date = :date, description = :description, category = :category, card = :card, amount = :amount
            WHERE id = :id AND user_id = :user_id
            RETURNING *;
        """

        values = {
            "date": transaction.date,
            "description": transaction.description,
            "category": transaction.category,
            "card": transaction.card,
            "amount": transaction.amount,
            "id": transaction.id,
            "user_id": user_id,
        }

        response = db.execute(text(query), values)

        data = response.mappings().first()

        if not data:
            db.rollback()
            raise HTTPException(status_code=404, detail="Transaction not found.")

        db.commit()
        #print("UPDATE DATA: ", data)

        return data

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        print("Error in updateTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to update transaction.")

@routerTransactions.delete("/deleteTransaction")
def deleteTransaction (transaction_id: int = Query(gt=0), dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        # this endpoint had no authentication and deleted by id only
        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to delete data.")

        query = """
            DELETE FROM transactions
            WHERE id = :id AND user_id = :user_id
            RETURNING *;
        """

        value = {"id": transaction_id, "user_id": dataUser["id"]}

        response = db.execute(text(query), value)

        data = response.mappings().first()

        if not data:
            db.rollback()
            raise HTTPException(status_code=404, detail="Transaction not found.")

        db.commit()
        #print(data)

        return data

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        print("Error in deleteTransactions: ", str(e))
        raise HTTPException(status_code=400, detail="Error to delete transaction.")
