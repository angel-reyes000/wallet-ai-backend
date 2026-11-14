from fastapi import Depends, APIRouter, HTTPException
from app.routers.users import authUser
from app.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import Card
import calendar
from datetime import datetime

routerCards = APIRouter(prefix="/cards", tags=["cards"])

@routerCards.get("/getTotalCardsBarChart")
def getTotalCardsBarChart(month: str = None, year: str = None, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        user_id = dataUser["id"]
        
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

    except Exception as e:
        print("Error in getTotalCardsBarChart: ", str(e))
        raise HTTPException(status_code=400, detail="Error to getTotalCardsBarChart")

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

    except Exception as e:
        print("Error in getCards: ", str(e))
        raise HTTPException(status_code=400, detail="Error to get cards.")

@routerCards.post("/postCard")
def updateCard (card: Card, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        user_id = dataUser["id"]

        if not card:
            raise HTTPException(status_code=400, detail="No hay registro que modificar.")

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

    except Exception as e:
        print("Error in postCards: ", str(e))
        raise HTTPException(status_code=400, detail="Error to post cards.")

@routerCards.put("/updateCard")
def updateCard (card: Card, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        if not card:
            raise HTTPException(status_code=400, detail="No hay registro que modificar.")

        query = """
            UPDATE cards
            SET 
            name = :name, 
            type = :type, 
            last_numbers = :last_numbers,
            expired_date = :expired_date,
            background_color = :background_color,
            color = :color
            WHERE id = :id
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
        }

        response = db.execute(text(query), values)
        db.commit()

        data = response.mappings().all()
        print(data)

        return data

    except Exception as e:
        print("Error in updateCards: ", str(e))
        raise HTTPException(status_code=400, detail="Error to update cards.")
