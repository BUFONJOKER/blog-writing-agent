from langchain_community.tools import DuckDuckGoSearchResults

# Initialize the tool
search = DuckDuckGoSearchResults()

# run() returns a string of results by default
results = search.run("Earth's core formation scientific consensus 2026")
print(results)