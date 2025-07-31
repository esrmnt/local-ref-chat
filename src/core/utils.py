"""
Utility functions for local-ref-chat.
General-purpose helpers for text cleaning, formatting, etc.
"""

def clean_text(text: str) -> str:
    """
    Normalize and clean text for indexing and search.
    Removes extra spaces, replaces non-breaking spaces.
    """
    return ' '.join(text.replace('\xa0', ' ').strip().split())

def format_snippet(snippet: str, max_length: int = 250) -> str:
    """
    Truncate a snippet and append ellipsis if too long.
    """
    return snippet if len(snippet) <= max_length else snippet[:max_length] + "..."

def render_citation(filename: str, chunk_index: int) -> str:
    """
    Format a user-friendly citation for a file and location.
    """
    return f"[Source: {filename}, chunk {chunk_index}]"
