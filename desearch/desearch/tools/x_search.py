from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from utils.desearch_client import X_SORTS, DesearchClient


def _post_summary(post: dict) -> dict:
    user = post.get("user") or {}
    return {
        "id": post.get("id"),
        "url": post.get("url"),
        "text": post.get("text"),
        "created_at": post.get("created_at"),
        "username": user.get("username"),
        "like_count": post.get("like_count"),
        "retweet_count": post.get("retweet_count"),
        "reply_count": post.get("reply_count"),
    }


class XSearchTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        query = str(tool_parameters.get("query") or "").strip()
        if not query:
            yield self.create_text_message("Please provide a search query.")
            return
        try:
            count = int(tool_parameters.get("count") or 10)
        except (TypeError, ValueError):
            count = 10
        count = max(1, min(100, count))
        sort = tool_parameters.get("sort") or "Top"
        if sort not in X_SORTS:
            sort = "Top"
        user = str(tool_parameters.get("user") or "").strip().lstrip("@") or None
        client = DesearchClient(self.runtime.credentials.get("api_key", ""), timeout=60)
        body = client.x_search(
            query,
            count=count,
            sort=sort,
            user=user,
            lang=tool_parameters.get("lang") or None,
            start_date=tool_parameters.get("start_date") or None,
            end_date=tool_parameters.get("end_date") or None,
        )
        posts = [_post_summary(p) for p in (body if isinstance(body, list) else []) if isinstance(p, dict)]
        if not posts:
            yield self.create_text_message(f"No X posts for: {query}")
            return
        text = "\n\n".join(f"@{p['username']} ({p['created_at']}): {p['text']}\n{p['url']}" for p in posts)
        yield self.create_text_message(text)
        yield self.create_json_message({"query": query, "posts": posts})
