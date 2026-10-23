from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.desearch_client import DesearchClient


class WebSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        query = str(tool_parameters.get("query") or "").strip()
        if not query:
            yield self.create_text_message("Please provide a search query.")
            return
        client = DesearchClient(self.runtime.credentials.get("api_key", ""), timeout=30)
        body = client.web_search(query, tool_parameters.get("start"))
        results = [
            {"title": r.get("title", ""), "link": r.get("link", ""), "snippet": r.get("snippet", "")}
            for r in (body.get("data") or [] if isinstance(body, dict) else [])
            if isinstance(r, dict)
        ]
        if not results:
            yield self.create_text_message(f"No web results for: {query}")
            return
        text = "\n\n".join(f"{i}. {r['title']}\n{r['link']}\n{r['snippet']}" for i, r in enumerate(results, 1))
        yield self.create_text_message(text)
        yield self.create_json_message({"query": query, "results": results})
