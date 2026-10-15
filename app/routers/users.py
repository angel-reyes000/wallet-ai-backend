from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.db import get_db
from sqlalchemy import text
from app.schemas import User
import bcrypt
import jwt
from dotenv import load_dotenv
import os

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

        hashed_password = bcrypt.hashpw(user.password.encode(), bcrypt.gensalt())

        values = {"username": user.username, "email": user.email, "password": hashed_password}

        response = db.execute(text(query), values)
        db.commit()

        data = response.mappings().first()
        #print(data)

        token = jwt.encode(dict(data), JWT_SECRET, algorithm="HS256")

        return [token, data]

    except Exception as e:
        print(f"Error in postUsers: {str(e)}")
        return {"message": "Error at create account."}
