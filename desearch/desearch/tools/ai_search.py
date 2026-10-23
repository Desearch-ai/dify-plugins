from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.desearch_client import DATE_FILTERS, DesearchClient, collect_links, parse_sources


class AiSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        prompt = str(tool_parameters.get("prompt") or "").strip()
        if not prompt:
            yield self.create_text_message("Please provide a prompt.")
            return
        sources = parse_sources(tool_parameters.get("sources"))
        date_filter = tool_parameters.get("date_filter") or None
        if date_filter and date_filter not in DATE_FILTERS:
            date_filter = None
        client = DesearchClient(self.runtime.credentials.get("api_key", ""), timeout=90)
        body = client.ai_search(prompt, sources, date_filter)
        answer = str(body.get("completion") or "").strip() if isinstance(body, dict) else ""
        links = collect_links(body)
        if not answer and not links:
            yield self.create_text_message(f"No AI search results for: {prompt}")
            return
        parts = [answer] if answer else []
        if links:
            parts.append("Sources:\n" + "\n".join(f"- {l['title']} {l['link']}".strip() for l in links))
        yield self.create_text_message("\n\n".join(parts))
        yield self.create_json_message({"prompt": prompt, "sources": sources, "answer": answer, "links": links})
