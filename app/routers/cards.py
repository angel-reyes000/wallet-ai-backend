from fastapi import Depends, APIRouter, HTTPException
from app.routers.users import authUser
from app.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import Card
from app.validation import period_filters
import calendar
from datetime import datetime

routerCards = APIRouter(prefix="/cards", tags=["cards"])

@routerCards.get("/getTotalCardsBarChart")
def getTotalCardsBarChart(period = Depends(period_filters), dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        user_id = dataUser["id"]
        month, year = period
        
        query = ""
        values = {}
        if (len(month) > 0 and len(year) > 0):
            query = """
                SELECT t.card, c.background_color, SUM(t.amount) AS total FROM transactions t 
                LEFT JOIN cards c ON t.card = c.name
                WHERE t.user_id = :user_id AND EXTRACT(MONTH FROM date) = :month AND EXTRACT(YEAR FROM date) = :year
                GROUP BY t.card, c.background_color;
            """
            values = {"user_id": user_id, "year": year, "month": month}
        elif (len(year) > 0):
            query = """
                SELECT t.card, c.background_color, SUM(t.amount) AS total FROM transactions t 
                LEFT JOIN cards c ON t.card = c.name
                WHERE t.user_id = :user_id AND EXTRACT(YEAR FROM date) = :year
                GROUP BY t.card, c.background_color;
            """
            values = {"user_id": user_id, "year": year}
        elif (len(month) > 0):
            raise HTTPException(status_code=400, detail="Can not filter only to month.")
        else:
            query = """
                SELECT t.card, c.background_color, SUM(t.amount) AS total FROM transactions t
                LEFT JOIN cards c ON t.card = c.name
                WHERE t.user_id = :user_id AND EXTRACT(YEAR FROM t.date)::INTEGER BETWEEN EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER - 10 AND EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER
                GROUP BY t.card, c.background_color;
            """
            values = {"user_id": user_id}

        response = db.execute(text(query), values)

        data = response.mappings().all()

        return data

    except HTTPException:
        raise

    except Exception as e:
        print("Error in getTotalCardsBarChart: ", str(e))
        raise HTTPException(status_code=400, detail="Error to getTotalCardsBarChart")

@routerCards.get("/getTotalToType")
def getTotalToType(period = Depends(period_filters), dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        user_id = dataUser["id"]
        month, year = period
        month = month or ""
        year = year or ""

        if (len(month) > 0 and len(year) > 0):
            where = "t.user_id = :user_id AND EXTRACT(MONTH FROM t.date) = :month AND EXTRACT(YEAR FROM t.date) = :year"
            values = {"user_id": user_id, "year": year, "month": month}
        elif (len(year) > 0):
            where = "t.user_id = :user_id AND EXTRACT(YEAR FROM t.date) = :year"
            values = {"user_id": user_id, "year": year}
        elif (len(month) > 0):
            raise HTTPException(status_code=400, detail="Can not filter only to month.")
        else:
            where = "t.user_id = :user_id AND EXTRACT(YEAR FROM t.date)::INTEGER BETWEEN EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER - 10 AND EXTRACT(YEAR FROM CURRENT_DATE)::INTEGER"
            values = {"user_id": user_id}

        # Card type: 'Credit', 'Debit' or NULL (no card match) -> 'Cash'
        query = f"""
            SELECT COALESCE(c.type, 'Cash') AS type,
                   COALESCE(SUM(t.amount), 0) AS total_money,
                   COUNT(t.id) AS total_moviments,
                   COALESCE(SUM(CASE WHEN t.amount > 0 THEN t.amount END), 0) AS total_incomes,
                   COALESCE(SUM(CASE WHEN t.amount < 0 THEN t.amount END), 0) AS total_expenses
            FROM transactions t
            LEFT JOIN cards c ON t.card = c.name
            WHERE {where}
            GROUP BY COALESCE(c.type, 'Cash');
        """

        response = db.execute(text(query), values)

        return response.mappings().all()

    except HTTPException:
        raise

    except Exception as e:
        print("Error in getTotalToType: ", str(e))
        raise HTTPException(status_code=400, detail="Error to getTotalToType")

@routerCards.get("/getCards")
def getCards(dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        user_id = dataUser["id"]        

        query = """SELECT * FROM cards WHERE user_id = :user_id"""

        value = {"user_id": user_id}

        response = db.execute(text(query), value)

        data = response.mappings().all()
        print("DATA CARDS: ", data)

        return data

    except HTTPException:
        raise

    except Exception as e:
        print("Error in getCards: ", str(e))
        raise HTTPException(status_code=400, detail="Error to get cards.")

def ensureUniqueCardName (db: Session, user_id: int, name: str, card_id = None):
    """Transactions point to a card by name, so two cards of one user can not share it."""
    if card_id:
        query = "SELECT 1 FROM cards WHERE user_id = :user_id AND LOWER(name) = LOWER(:name) AND id <> :id"
        values = {"user_id": user_id, "name": name, "id": card_id}
    else:
        query = "SELECT 1 FROM cards WHERE user_id = :user_id AND LOWER(name) = LOWER(:name)"
        values = {"user_id": user_id, "name": name}

    if db.execute(text(query), values).first():
        raise HTTPException(status_code=400, detail="You already have a card with that name.")

@routerCards.post("/postCard")
def updateCard (card: Card, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        user_id = dataUser["id"]

        # every field was already validated by the Card schema
        ensureUniqueCardName(db, user_id, card.name)

        query = """
            INSERT INTO cards (
                name,
                type,
                last_numbers,
                expired_date,
                background_color,
                color,
                user_id
            ) VALUES (
                :name,
                :type,
                :last_numbers,
                :expired_date,
                :background_color,
                :color,
                :user_id
            ) RETURNING *;
        """

        values = {
            "name": card.name,
            "type": card.type,
            "last_numbers": card.last_numbers,
            "expired_date": (card.expired_date + "-01"),
            "background_color": card.background_color,
            "color": card.color,
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
        print("Error in postCards: ", str(e))
        raise HTTPException(status_code=400, detail="Error to post cards.")

@routerCards.put("/updateCard")
def updateCard (card: Card, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        if not card.id:
            raise HTTPException(status_code=400, detail="No hay registro que modificar.")

        user_id = dataUser["id"]

        ensureUniqueCardName(db, user_id, card.name, card.id)

        # user_id in the WHERE: a user can only edit their own cards
        query = """
            UPDATE cards
            SET
            name = :name,
            type = :type,
            last_numbers = :last_numbers,
            expired_date = :expired_date,
            background_color = :background_color,
            color = :color
            WHERE id = :id AND user_id = :user_id
            RETURNING *;
        """

        values = {
            "name": card.name,
            "type": card.type,
            "last_numbers": card.last_numbers,
            "expired_date": (card.expired_date + "-01"),
            "background_color": card.background_color,
            "color": card.color,
            "id": card.id,
            "user_id": user_id,
        }

        response = db.execute(text(query), values)

        data = response.mappings().all()

        if not data:
            db.rollback()
            raise HTTPException(status_code=404, detail="Card not found.")

        db.commit()
        print(data)

        return data

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        print("Error in updateCards: ", str(e))
        raise HTTPException(status_code=400, detail="Error to update cards.")
