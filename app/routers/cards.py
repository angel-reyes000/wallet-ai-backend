from fastapi import Depends, APIRouter, HTTPException
from app.routers.users import authUser
from app.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import Card

routerCards = APIRouter(prefix="/cards", tags=["cards"])

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

@routerCards.put("/updateCard")
def updateCard (card: Card, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error al obtener datos de usuario.")

        user_id = dataUser["id"]

        if not card:
            raise HTTPException(status_code=400, detail="No hay registro que modificar.")

        query = """
            UPDATE cards
            SET 
            name = :name, 
            type = :type, 
            last_numbers = :last_numbers,
            expired_date = :expired_date,
            color = :color
            WHERE id = :id
            RETURNING *;            
        """        

        values = {
            "name": card.name,
            "type": card.type,
            "last_numbers": card.last_numbers,
            "expired_date": card.expired_date,
            "color": card.color,
            "id": card.id,
        }

        response = db.execute(text(query), values)
        db.commit()

        data = response.mappings().all()
        print(data)

        return data

    except Exception as e:
        print("Error in getCards: ", str(e))
        raise HTTPException(status_code=400, detail="Error to get cards.")
