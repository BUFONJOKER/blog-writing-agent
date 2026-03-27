import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch
from tools.fetch_page import fetch_page_tool
from tools.web_search import web_search_tool
from tools.keyword_extractor import extract_keywords_tool
from tools.summarizer import summarize_research

# --- WEB SEARCH TESTS ---
@pytest.mark.asyncio
async def test_web_search_success(mocker):
    # Mock Tavily response
    mock_response = {
        "results": [{"url": "http://test.com", "title": "Test", "content": "Context", "score": 0.9}]
    }
    mocker.patch("tavily.TavilyClient.search", return_value=mock_response)

    result = web_search_tool("Python 3.13")
    assert "url" in result
    assert result["title"] == "Test"

def test_web_search_empty_input():
    with pytest.raises(ValueError, match="Query must be a non-empty string"):
        web_search_tool("  ")

# --- FETCH PAGE TESTS ---
@pytest.mark.asyncio
async def test_fetch_page_invalid_url():
    with pytest.raises(Exception): # Adjust based on your specific error handling
        fetch_page_tool("not-a-url", "topic")

# --- KEYWORD EXTRACTION TESTS ---
def test_extract_keywords_format():
    text = "Python is a programming language used for data science and machine learning."
    # The tool returns a 'Directive' string, not the list directly
    result = extract_keywords_tool(text, "Python", max_keywords=5)
    assert "### SEO EXTRACTION TASK ###" in result
    assert "JSON array of 5" in result

# --- SUMMARIZATION TESTS ---
def test_summarize_efficiency_path():
    short_text = "This is a very short sentence."
    # Should skip the heavy directive and return the text as is
    result = summarize_research(short_text, "test", max_words=100)
    assert "PRE-OPTIMIZED CONTENT" in result

def test_summarize_long_input():
    long_text = "Data Science " * 100
    result = summarize_research(long_text, "Data Science", max_words=50)
    assert "### TECHNICAL SUMMARIZATION DIRECTIVE ###" in result