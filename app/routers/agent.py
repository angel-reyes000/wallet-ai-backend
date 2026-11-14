from fastapi import APIRouter, Depends, HTTPException
from app.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.routers.users import authUser
from app.schemas import Message
from app.schemas import AgentReply
from langchain.chat_models import init_chat_model
from app.agent.agents import general_agent, ragAgent
from langgraph_supervisor import create_supervisor
from app.agent.agentConfig import model, temperature
from app.agent.prompts import promptSupervisorAgent
from uuid import uuid4
from dotenv import load_dotenv
import os

load_dotenv()

routerAgent = APIRouter(prefix="/agent", tags=["agent"])

API_DEEPSEEK = os.getenv("API_DEEPSEEK")

llm = init_chat_model(model=model, temperature=temperature, api_key=API_DEEPSEEK, extra_body={"thinking": {"type": "disabled"}})


@routerAgent.get("/getMessages")
def getMessages (dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try: 

        if not dataUser:
            return HTTPException(status_code=400, detail="Error to get Messages. log in again.")

        user_id = dataUser["id"]

        query = """
            SELECT * FROM messages WHERE user_id = :id 
            ORDER BY id ASC
            LIMIT 50
        """

        value = {"id": user_id}

        response = db.execute(text(query), value)

        data = response.mappings().all()
        #print("MESSAGES: ", data)

        return data

    except Exception as e:
        print("Error in getMessages: ", str(e))
        return HTTPException(status_code=400, detail="Login again.")

def getHistory (dataUser, db):
    try: 

        if not dataUser:
            return HTTPException(status_code=400, detail="Error to get History. log in again.")

        user_id = dataUser["id"]

        query = """
            SELECT role, message AS content FROM messages 
            WHERE user_id = :id 
            ORDER BY id ASC
            LIMIT 50
        """

        value = {"id": user_id}

        response = db.execute(text(query), value)

        data = [dict(obj) for obj in response.mappings().all()]
        print("MESSAGES: ", data)

        return data

    except Exception as e:
        print("Error in getHistory: ", str(e))
        return HTTPException(status_code=400, detail="Login again.")

@routerAgent.post("/postMessage")
def postMessage (dataMessage: Message, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            raise HTTPException(status_code=400, detail="Error to post message. login again")

        user_id = dataUser["id"] 

        history = getHistory(dataUser=dataUser, db=db)
        print("HISTORYYY: ", history)

        if not isinstance(history, list):
            raise HTTPException(status_code=400, detail="Error to get history.")        

        agent_supervisor = create_supervisor(
            model=llm,
            agents=[general_agent, ragAgent],
            prompt=promptSupervisorAgent,
            response_format=AgentReply,
        )    

        compiled_agent = agent_supervisor.compile()

        config = {"configurable": {"thread_id": str(uuid4()), "user_id": user_id, "db": db}}

        response_agent = compiled_agent.invoke({"messages": history + [{"role": "user", "content": dataMessage.message}]}, config)

        final_answer = response_agent["messages"][-1].content

        query = """INSERT INTO messages (role, message, user_id)
            VALUES (:role, :message, :user_id)
            RETURNING *
        """

        values_user = {"role": "user", "message": dataMessage.message, "user_id": user_id} 
        db.execute(text(query), values_user)

        values_ai = {"role": "ai", "message": final_answer, "user_id": user_id} 
        response_llm = db.execute(text(query), values_ai)

        data_llm = response_llm.mappings().first()

        db.commit()

        return data_llm

    except Exception as e:
        print("Error in postMessage: ", str(e))
        raise HTTPException(status_code=400, detail="Error to post message.")