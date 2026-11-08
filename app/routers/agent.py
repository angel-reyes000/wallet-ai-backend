from fastapi import APIRouter, Depends, HTTPException
from app.database.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.routers.users import authUser
from app.schemas import Message
from langchain.chat_models import init_chat_model
from app.agent.agents import general_agent
from langgraph_supervisor import create_supervisor
from app.agent.agentConfig import model, temperature
from app.vectorestore.chromaDB import vectorstore
from uuid import uuid4
from dotenv import load_dotenv
import json
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

        query = """SELECT * FROM messages WHERE user_id = :id"""

        value = {"id": user_id}

        response = db.execute(text(query), value)

        data = response.mappings().all()
        print(data)

        return data

    except Exception as e:
        print("Error in getMessages: ", str(e))
        return HTTPException(status_code=400, detail="Login again.")

def add_text (dataMessage: Message):
    vectorstore.add_texts(
        texts=[dataMessage.text],
        metadatas=[{"role": dataMessage.role}],
        ids=[uuid4()]
    )

def search_text (dataMessage):
    retriever = vectorstore.as_retriever(search_type="similarity",  search_kwargs={"k": 5})

    response = retriever.invoke(dataMessage["message"])
    print(response)
    search_similarities = []

    for doc in response:
        print(doc)
        search_similarities.append(doc.page_content)
        print(doc.page_content)

    if len(search_similarities) > 0:
        return search_similarities
    else:
        if len(search_similarities) <= 1:
            add_text()
        return "There aren't similar context."

@routerAgent.post("/postMessage")
def postMessage (dataMessage: Message, dataUser = Depends(authUser), db: Session = Depends(get_db)):
    try:

        if not dataUser:
            return HTTPException(status_code=400, detail="Error to post message. login again")

        user_id = dataUser["id"] 

        agent_supervisor = create_supervisor(
            model=llm,
            agents=[general_agent],
            prompt="""
                Choose the best agent to response at the user, always only
                return the same json schema that return the agent, no more.

                Follow the next rules:
                    - Always use the tool 'memory_tool' from 'general_agent' to answer.
                    - Always to response based in the two last messages (ai and user) that return 'memory_tool'.
                    - Always return the json schema: {"role": "ai", "message": <your answer>}                    
                    
                the structure have be the next:

                {
                    "role": "ai",
                    "message": <your answer>
                }

            """,
        )    

        compiled_agent = agent_supervisor.compile()

        config = {"configurable": {"thread_id": str(uuid4()), "user_id": user_id, "db": db}}

        response_agent = compiled_agent.invoke({"messages": [{"role": "user", "content": dataMessage.message}]}, config)
        #print("AGENT RESPONSE: ", response_agent["messages"][-1].content)

        final_answer = json.loads(response_agent["messages"][-1].content)

        query = """INSERT INTO messages (role, message, user_id)
            VALUES (:role, :message, :user_id)
            RETURNING *
        """

        values_user = {"role": "user", "message": dataMessage.message, "user_id": user_id} 
        db.execute(text(query), values_user)
        #print("USER MESSAGE: ", dataMessage.message)

        values_ai = {"role": "ai", "message": final_answer["message"], "user_id": user_id} 
        response_llm = db.execute(text(query), values_ai)

        data_llm = response_llm.mappings().first()

        db.commit()

        #print("RESPUESTA FINAL: ", final_answer)
        #print("LLM RESPONSE: ", data_llm)
        return data_llm

    except Exception as e:
        print("Error in postMessage: ", str(e))
        return HTTPException(status_code=400, detail="Error to post message.")