from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.db import get_db
from app.routers.users import authUser
from app.schemas import UserSettings

routerSettings = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_SETTINGS = {"temperature": 0.5, "theme": "dark"}

def getUserSettings (db: Session, user_id: int) -> dict:
    """Never raises: the chat must keep working with defaults if settings are unavailable."""
    try:
        row = db.execute(
            text("SELECT temperature, theme FROM user_settings WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).mappings().first()

        if not row:
            return dict(DEFAULT_SETTINGS)

        return {"temperature": float(row["temperature"]), "theme": row["theme"]}

    except Exception as e:
        db.rollback()
        print("Error in getUserSettings: ", str(e))
        return dict(DEFAULT_SETTINGS)

@routerSettings.get("/getSettings")
def getSettings (dataUser = Depends(authUser), db: Session = Depends(get_db)):
    if not dataUser:
        raise HTTPException(status_code=400, detail="Session expired.")

    return getUserSettings(db, dataUser["id"])

@routerSettings.put("/updateSettings")
def updateSettings (dataSettings: UserSettings, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Session expired.")

        query = """
            INSERT INTO user_settings (user_id, temperature, theme)
            VALUES (:user_id, :temperature, :theme)
            ON CONFLICT (user_id) DO UPDATE
            SET temperature = EXCLUDED.temperature, theme = EXCLUDED.theme
            RETURNING temperature, theme
        """

        values = {
            "user_id": dataUser["id"],
            "temperature": round(dataSettings.temperature, 1),
            "theme": dataSettings.theme,
        }

        row = db.execute(text(query), values).mappings().first()

        db.commit()

        return {"temperature": float(row["temperature"]), "theme": row["theme"]}

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        print("Error in updateSettings: ", str(e))
        raise HTTPException(status_code=400, detail="Error to update settings.")
