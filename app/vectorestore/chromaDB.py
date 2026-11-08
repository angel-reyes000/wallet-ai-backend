import chromadb
from langchain_chroma import Chroma
from chromadb.api import ClientAPI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from fastapi import HTTPException, Depends
from dotenv import load_dotenv
import os

load_dotenv()

CHROMA_API=os.getenv("CHROMA_API")
CHROMA_TENANT=os.getenv("CHROMA_TENANT")
CHROMA_DATABASE=os.getenv("CHROMA_DATABASE")

def get_chroma_client () -> ClientAPI:
    try: 

        client = chromadb.CloudClient(
            api_key=CHROMA_API,
            tenant=CHROMA_TENANT,
            database=CHROMA_DATABASE
        )

        return client

    except Exception as e:
        print("Error to get client chroma db.")
        raise HTTPException(status_code=400, detail="Error to client chroma db.")

vectorstore = Chroma(
    client=get_chroma_client(),
    collection_name="messages",
    embedding_function=GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2",
        api_key=os.getenv("API_GEMINI")
    ),
)