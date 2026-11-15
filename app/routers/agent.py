from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder
from langchain_core.messages import AIMessageChunk
from app.database.db import get_db, session as SessionLocal
import json
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.routers.users import authUser
from app.schemas import Message
from app.schemas import AgentReply
from langchain.chat_models import init_chat_model
from app.agent.agents import general_agent, ragAgent
from langgraph_supervisor import create_supervisor
from app.agent.agentConfig import model, temperature
from app.routers.settings import getUserSettings
from app.agent.prompts import promptSupervisorAgent
from uuid import uuid4
from dotenv import load_dotenv
import os

load_dotenv()

routerAgent = APIRouter(prefix="/agent", tags=["agent"])

API_DEEPSEEK = os.getenv("API_DEEPSEEK")

llm = init_chat_model(model=model, temperature=temperature, api_key=API_DEEPSEEK, extra_body={"thinking": {"type": "disabled"}})

def buildLlm (user_temperature: float):
    """Supervisor model using the temperature the user chose in Configuration."""
    return init_chat_model(model=model, temperature=user_temperature, api_key=API_DEEPSEEK, extra_body={"thinking": {"type": "disabled"}})


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
            model=buildLlm(getUserSettings(db, user_id)["temperature"]),
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

def sse (payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

def chunk_text (chunk) -> str:
    content = chunk.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )

    return ""

def is_supervisor_token (chunk, namespace) -> bool:
    """Only the supervisor's final text is the answer shown to the user:
    skip sub-agents, tool calls and handoff messages."""
    if not isinstance(chunk, AIMessageChunk) or chunk.tool_call_chunks:
        return False

    return len(namespace) > 0 and namespace[0].startswith("supervisor")

def stream_agent (history, message: str, user_id, db):
    """Yields ("token", text) while the supervisor answers and ("final", text) at the end."""
    agent_supervisor = create_supervisor(
        model=buildLlm(getUserSettings(db, user_id)["temperature"]),
        agents=[general_agent, ragAgent],
        prompt=promptSupervisorAgent,
    )

    compiled_agent = agent_supervisor.compile()

    config = {"configurable": {"thread_id": str(uuid4()), "user_id": user_id, "db": db}}

    last_state = None

    # subgraphs=True is required: the supervisor LLM runs inside a subgraph, and
    # without it LangGraph only emits the complete message instead of tokens.
    for namespace, mode, payload in compiled_agent.stream(
        {"messages": history + [{"role": "user", "content": message}]},
        config,
        stream_mode=["messages", "values"],
        subgraphs=True,
    ):
        if mode == "messages":
            chunk, _metadata = payload
            if is_supervisor_token(chunk, namespace):
                piece = chunk_text(chunk)
                if piece:
                    yield "token", piece
        elif mode == "values" and not namespace:
            last_state = payload

    if last_state is None:
        raise RuntimeError("Agent returned no state.")

    yield "final", last_state["messages"][-1].content

@routerAgent.post("/postMessageStream")
def postMessageStream (dataMessage: Message, dataUser = Depends(authUser)):
    if not dataUser:
        raise HTTPException(status_code=400, detail="Error to post message. login again")

    user_id = dataUser["id"]

    def event_stream ():
        # Own session: the request-scoped one may be closed before the stream ends.
        db = SessionLocal()

        try:

            history = getHistory(dataUser=dataUser, db=db)

            if not isinstance(history, list):
                yield sse({"error": "Error to get history."})
                return

            final_answer = None

            for kind, piece in stream_agent(history, dataMessage.message, user_id, db):
                if kind == "token":
                    yield sse({"token": piece})
                else:
                    final_answer = piece

            query = """INSERT INTO messages (role, message, user_id)
                VALUES (:role, :message, :user_id)
                RETURNING *
            """

            db.execute(text(query), {"role": "user", "message": dataMessage.message, "user_id": user_id})
            response_llm = db.execute(text(query), {"role": "ai", "message": final_answer, "user_id": user_id})

            data_llm = response_llm.mappings().first()

            db.commit()

            yield sse({"done": True, "message": jsonable_encoder(dict(data_llm))})

        except Exception as e:
            db.rollback()
            print("Error in postMessageStream: ", str(e))
            yield sse({"error": "Error to post message."})

        finally:
            db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
