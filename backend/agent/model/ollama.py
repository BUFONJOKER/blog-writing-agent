from langchain_ollama import ChatOllama

def load_model():
    '''
    Load the Ollama model using the ChatOllama class from langchain_ollama.
    '''

    model = ChatOllama(model="qwen3.5:cloud")

    return model