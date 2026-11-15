from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from sqlalchemy import text
from app.schemas import User, LoginUser
import bcrypt
import jwt
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from fastapi.encoders import jsonable_encoder

JWT_SECRET = os.getenv("JWT_SECRET")

routerUsers = APIRouter(prefix="/users", tags=["users"])

@routerUsers.post("/postUser")
def postUser(user: User, db: Session = Depends(get_db)):

    try:

        # user.username / email / password were already validated and cleaned by the schema.
        queryCheckEmail = "SELECT email FROM users WHERE LOWER(email) = LOWER(:email)"

        emailValue = {"email": user.email}

        responseEmail = db.execute(text(queryCheckEmail), emailValue)

        existEmail = responseEmail.mappings().all()

        if len(existEmail) >= 1:
            return {"message": "Already email exists."}

        query = """INSERT INTO users (username, email, password)
                   VALUES (:username, :email, :password)
                   RETURNING *
                """

        hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt()).decode()

        values = {"username": user.username, "email": user.email, "password": hashed_password}

        response = db.execute(text(query), values)
        db.commit()

        data = response.mappings().first()
        #print(data)

        return {}

    except Exception as e:
        db.rollback()
        print(f"Error in postUsers: {str(e)}")
        return {"message": "Error at create account."}

def authUser (authorization: str = Header()):
    try:

        token = authorization.removeprefix("Bearer ").strip()

        if not token:
            # falsy like every other auth failure: the endpoints answer "Session expired"
            return False

        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

    except jwt.ExpiredSignatureError:
        print("Invalid token, sesison expired.")
        return False
        #{"message": "Session expired"}

    except Exception as e:
        print(f"Error in authUsers: {str(e)}")
        return False
        #{"message": "Error in authUsers."}

@routerUsers.get("/getUsers")
def getUsers(dataUser = Depends(authUser), db: Session = Depends(get_db)):
    # This endpoint used to list every user, password hashes included, without a token.
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Session expired.")

        query = "SELECT id, username, email, created_at FROM users WHERE id = :id"

        response = db.execute(text(query), {"id": dataUser["id"]})

        return response.mappings().all()

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error in getUsers: {str(e)}")
        raise HTTPException(status_code=400, detail="Error in getUsers.")

@routerUsers.get("/getDataUser")
def getDataUser(dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Session expired.")

        query = "SELECT username, email, created_at FROM users WHERE id = :id"

        value = {"id": dataUser["id"]}

        response = db.execute(text(query), value)

        data = response.mappings().first()

        return data

    except Exception as e:
        print(f"Error in getDataUsers: {str(e)}")
        #return {"message": "Error to get data"}
        raise HTTPException(status_code=400, detail="Error to get data.")

@routerUsers.post('/verifyUser')
def verifyUser (user: LoginUser, db: Session = Depends(get_db)):
    try:

        query = "SELECT * FROM users WHERE LOWER(email) = LOWER(:email)"

        value = {"email": user.email}

        response = db.execute(text(query), value)

        data = response.mappings().all()

        if len(data) <= 0:
            return {"message": "User not exist."}

        dataUser = dict(data[0])

        checkPassword = bcrypt.checkpw(user.password.encode(), dataUser["password"].encode())

        if not checkPassword:
            return {"message": "Invalid password."}

        dataUser.pop("password")
        dataUser["created_at"] = str(dataUser["created_at"])

        payload = dataUser
        payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=1)

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        print(token)

        return token

    except Exception as e:
        print(f"Error in verifyUsers: {str(e)}")
        return {"message": "Error to auth."}
