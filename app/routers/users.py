from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database.db import get_db
from sqlalchemy import text
from app.schemas import User
import bcrypt
import jwt
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone

JWT_SECRET = os.getenv("JWT_SECRET")

routerUsers = APIRouter(prefix="/users", tags=["users"])

@routerUsers.get("/getUsers")
def getUsers(db: Session = Depends(get_db)):
    try:

        query = "SELECT * FROM users"

        response = db.execute(text(query))

        data = response.mappings().all()

        return data

    except Exception as e:
        print(f"Error in getUsers: {str(e)}")
        return {"message": "Error in getUsers."}

@routerUsers.post("/postUser")
def postUser(user: User, db: Session = Depends(get_db)):

    try:

        queryCheckEmail = "SELECT email FROM users WHERE email = :email"

        emailValue = {"email": user.email}

        responseEmail = db.execute(text(queryCheckEmail), emailValue)

        existEmail = responseEmail.mappings().all()

        if not user.username:
            return {"message": "Invalid username."}
        
        elif not user.email:
            return {"message": "Invalid email."}

        elif len(existEmail) >= 1:
            return {"message": "Already email exists."}
        
        elif len(user.password) < 8 or not user.password:
            return {"message": "Invalid password."}        

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
        print(f"Error in postUsers: {str(e)}")
        return {"message": "Error at create account."}

def authUser (authorization: str = Header()):
    try:

        token = authorization.removeprefix("Bearer ")

        if not token: 
            return {"message": "Access denegade: Invalid token"}

        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

    except jwt.ExpiredSignatureError:
        print("Invalid token, sesison expired.")
        return False
        #{"message": "Session expired"}

    except Exception as e:
        print(f"Error in authUsers: {str(e)}")
        return False
        #{"message": "Error in authUsers."}

@routerUsers.get("/getDataUser")
def getDataUser(dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Session expired.")

        query = "SELECT username, email FROM users WHERE id = :id"

        value = {"id": dataUser["id"]}

        response = db.execute(text(query), value)

        data = response.mappings().first()

        return data

    except Exception as e:
        print(f"Error in getDataUsers: {str(e)}")
        #return {"message": "Error to get data"}
        raise HTTPException(status_code=400, detail="Error to get data.")

@routerUsers.post('/verifyUser')
def verifyUser (user: User, db: Session = Depends(get_db)):
    try:

        if not user.email or not user.password:
            return {"message": "Invalid data."}

        query = "SELECT * FROM users WHERE email = :email"

        value = {"email": user.email}

        response = db.execute(text(query), value)

        data = response.mappings().all()
        print(data[0])

        if len(data) <= 0:
            return {"message": "User not exist."}

        dataUser = data[0]

        checkPassword = bcrypt.checkpw(user.password.encode(), dataUser["password"].encode())

        if not checkPassword:
            return {"message": "Invalid password."}

        payload = dict(dataUser)
        payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=1) 

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        print(token)

        return token

    except Exception as e:
        print(f"Error in verifyUsers: {str(e)}")
        return {"message": "Error to auth."}