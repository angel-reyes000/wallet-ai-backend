from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import text
from app.vectorstore.chromaDB import get_chroma_client
from app.agent.agentConfig import API_GEMINI

@tool
def memory_tool(config: RunnableConfig) :
    """
        memory_tool:
        Recupera el contexto de la conversacion, usalo siempre en 
        cada mensaje para poder responderle al usuario.
    """

    user_id = config["configurable"]["user_id"]
    db = config["configurable"]["db"]

    query = """SELECT * FROM messages WHERE user_id = :user_id"""

    value = {"user_id": user_id}

    response = db.execute(text(query), value)

    data = response.mappings().all()

    return f"This is the context chat: \n{data}"

@tool
def query_tool(query: str, config: RunnableConfig):
    """
        query_tool:
        Crea consultas en base a lo que te pida el usuario
        cuando el usuario te pida consultar sus datos basandote
        en las tablas.

        Tables:
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                password TEXT NOT NULL,
                created_at DATE NOT NULL DEFAULT CURRENT_DATE
            );

            CREATE TABLE transactions (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(30) NOT NULL,
                type VARCHAR(30) NOT NULL,
                amount DECIMAL(9, 2) NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

        Argument: query
            - Have be a text string.
            - The query have be a only query, neither more nor less.
            - Siempre usa 'WHERE id = :user_id' no te preocupes por su id, ese lo proporciono yo.
            - Las consultas parametrizadas deben llevar = ':user_id' porque usamos FastAPI.
            - Solamente puedes realizar SELECT E INSERT y nada mas.
            - Si haras un 'INSERT' agrega 'RETURNING *' al final.

        - No hagas preguntas, simplemente realiza lo que se te pide.
        - No respondas otra cosa mas que con un query para realizar lo que se te pide.
    """

    user_id = config["configurable"]["user_id"]
    db = config["configurable"]["db"]

    value = {"user_id": user_id}

    response = db.execute(text(query), value)

    data = response.mappings().all()

    return f"Query: \n {data}"

@tool
def rag_tool(text: str):
    """
        Recupera toda la informacion sobre la app, como funciona,
        que es, para que usarla, como usarla, etc. 
    """

    vectorstore = Chroma(
        client=get_chroma_client(),
        embedding_function=GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-2",
            api_key=API_GEMINI,
        ),
        collection_name="about_wallet_ai",
    )

    response = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    result = response.invoke(text)

    return result

@tool
def data_finance_tool(text:str):
    """
    Eres un experto en finanzas y finanzas personales, daras consejos,
    retroalimentacion, motivacion, verdad y todo esto basado en finanzas.
    """
    return text