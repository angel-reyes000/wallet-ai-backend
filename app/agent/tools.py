from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlalchemy import text

@tool
def memory_tool(config: RunnableConfig) :
    """
        memory_tool:
        Retrieve user messages to remember past conversations
        and retrieve context to response at user.
    """

    user_id = config["configurable"]["user_id"]
    db = config["configurable"]["db"]

    query = """SELECT * FROM messages WHERE user_id = :user_id"""

    value = {"user_id": user_id}

    response = db.execute(text(query), value)

    data = response.mappings().all()

    return data