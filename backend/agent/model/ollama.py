from langchain_ollama import ChatOllama
from functools import lru_cache

@lru_cache(maxsize=1)
def load_model():
    '''
    Load the Ollama model using the ChatOllama class from langchain_ollama.
    '''

    model = ChatOllama(model="qwen3.5:cloud",temperature=0)

    return model