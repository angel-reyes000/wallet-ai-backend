from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

HOST_DB=os.getenv("HOST_DB")
PORT_DB=os.getenv("PORT_DB")
USER_DB=os.getenv("USER_DB")
PASSWORD_DB=os.getenv("PASSWORD_DB")
NAME_DB=os.getenv("NAME_DB")

URL_DB = "postgresql+psycopg2://postgres:dokirey1@localhost:5432/wallet-ai"

engine = create_engine(URL_DB)

session = sessionmaker(bind=engine, expire_on_commit=False)

def get_db ():
    try:
        get_session = session()
        print("Running session")
        yield get_session

    except Exception as e:
        print(f"Error in get_db: {str(e)}")
        raise

    finally:
        get_session.close()
        print("Closed session")
        