from langchain_openai import ChatOpenAI # pip install langchain-openai

llm = ChatOpenAI(
    model="qwen3.5:cloud", # Ollama will map this correctly
    openai_api_key="ollama", # Ollama ignores this, but it's required by the class
    base_url="https://alphabet-struck-underfed.ngrok-free.dev/v1", # Note the /v1
    default_headers={
        "ngrok-skip-browser-warning": "true",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
)

def main():
    try:
        print(f"--- Calling {llm.model} via Ngrok ---")
        response = llm.invoke("Summarize the benefits of Agentic Workflows.")
        print("\nAgent Output:\n", response.content)
    except Exception as e:
        print(f"\n[Error]: {e}")

if __name__ == "__main__":
    main()