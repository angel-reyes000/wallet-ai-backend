from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from app.vectorestore.chromaDB import get_chroma_client
from dotenv import load_dotenv
import os

#Run on terminal to add documents: python -m app.vectorestore.add_documents

load_dotenv()

API_GEMINI = os.getenv("API_GEMINI")

loader = PyPDFLoader(r"C:\Users\ar731\Downloads\Wallet-AI-Guia-Usuario.pdf")

documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=300,
)

doc_split = text_splitter.split_documents(documents)

vectorstore = Chroma.from_documents(
    documents=doc_split,
    embedding=GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2",
        api_key=API_GEMINI
    ),
    collection_name="about_wallet_ai",
    client=get_chroma_client(),
)

result = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

response = result.invoke("Dime como inicio sesion en la app?")

# for doc in response:
#     print(doc.page_content, "\n\n")


