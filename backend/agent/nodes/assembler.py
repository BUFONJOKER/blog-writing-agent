from langchain_core.prompts import ChatPromptTemplate
from agent.model import load_model
from agent.state import BlogAgentState

def assembler_node(state: BlogAgentState) -> dict:
    print(state['tasks_output'])
    pass