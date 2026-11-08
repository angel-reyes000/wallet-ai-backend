from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os

load_dotenv()

model = "deepseek:deepseek-flash"

temperature = 0.5

API_DEEPSEEK = os.getenv("API_DEEPSEEK")

llm = init_chat_model(
    model=model, 
    temperature=temperature, 
    api_key=API_DEEPSEEK, 
    extra_body={"thinking": {"type": "disabled"}}
)