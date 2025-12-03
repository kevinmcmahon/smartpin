# ABOUTME: Handles web page content extraction and bookmark data generation
# ABOUTME: Uses Claude Sonnet 4.0 to analyze pages and extract metadata

import json
from typing import Any

import httpx
import llm
from bs4 import BeautifulSoup
from jinja2 import Template


class PinboardBookmarkExtractor:
    """Extracts bookmark metadata from web pages using Claude Sonnet."""

    def __init__(self, model_name: str = "claude-opus-4.5") -> None:
        self.model = llm.get_model(model_name)
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )

        self.system_prompt = """You are a bookmark extraction assistant. Analyze the provided web page content and extract bookmark data.
Extract these four fields:
- title: The main title/headline of the page (not the HTML title tag, but the actual content title)
- url: The original URL provided
- description: A concise 1-2 sentence summary of what the page is about
- tags: An array of 3-8 relevant lowercase tags (use hyphens for multi-word tags)
CRITICAL: Return ONLY the JSON object with no additional text, explanations, code fences, or markdown formatting. Your entire response must be valid JSON that can be parsed directly."""

        self.prompt_template = Template(
            """Analyze this web page content to create a Pinboard bookmark entry:

URL: {{ url }}

Page Title: {{ page_title }}

Page Content:
{{ content }}

Extract the bookmark data as JSON."""
        )

    def fetch_page_content(self, url: str) -> tuple[str, str]:
        """
        Fetch and extract text content from a web page.

        Args:
            url: The URL to fetch

        Returns:
            Tuple of (page_title, content_text)

        Raises:
            httpx.HTTPError: If the request fails
        """
        response = self.client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        page_title = (
            str(soup.title.string) if soup.title and soup.title.string else "No title"
        )

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = " ".join(chunk for chunk in chunks if chunk)

        # Limit content length to avoid token limits
        max_chars = 10000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."

        return page_title, text

    def extract_bookmark(self, url: str) -> dict[str, Any]:
        """
        Extract bookmark data from a URL.

        Args:
            url: The URL to analyze

        Returns:
            Dictionary with title, url, description, and tags

        Raises:
            ValueError: If the response cannot be parsed as JSON
            httpx.HTTPError: If the web page cannot be fetched
        """
        # Fetch the actual page content
        page_title, content = self.fetch_page_content(url)

        # Create prompt with actual content
        prompt = self.prompt_template.render(
            url=url, page_title=page_title, content=content
        )

        response = self.model.prompt(prompt, system=self.system_prompt)

        try:
            bookmark_data: dict[str, Any] = json.loads(response.text().strip())
            return bookmark_data
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON response: {e}\nResponse was: {response.text()}"
            ) from e

    def __del__(self) -> None:
        """Clean up the HTTP client."""
        if hasattr(self, "client"):
            self.client.close()
