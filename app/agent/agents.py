from langchain.agents import create_agent
from app.agent.tools import memory_tool, query_tool
from langchain.chat_models import init_chat_model
from app.agent.agentConfig import API_DEEPSEEK
from app.schemas import AgentReply
from app.agent.prompts import promptGeneralAgent

llm = init_chat_model(model="deepseek:deepseek-flash", temperature=0.5, api_key=API_DEEPSEEK, extra_body={"thinking": {"type": "disabled"}})

general_agent = create_agent(
    name="general_agent",
    model=llm,
    tools=[memory_tool, query_tool],
    system_prompt=promptGeneralAgent,
)