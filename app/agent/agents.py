from langchain.agents import create_agent
from app.agent.tools import query_tool
from langchain.chat_models import init_chat_model
from app.agent.agentConfig import API_DEEPSEEK
from app.agent.prompts import promptGeneralAgent, promptRagAgent
from app.agent.tools import rag_tool, data_finance_tool

llm = init_chat_model(model="deepseek:deepseek-flash", temperature=0.5, api_key=API_DEEPSEEK, extra_body={"thinking": {"type": "disabled"}})

general_agent = create_agent(
    name="general_agent",
    model=llm,
    tools=[query_tool],
    system_prompt=promptGeneralAgent,
)

ragAgent = create_agent(
    name="aboutOfAppAgent",
    model=llm,
    tools=[rag_tool, data_finance_tool],
    system_prompt=promptRagAgent
)