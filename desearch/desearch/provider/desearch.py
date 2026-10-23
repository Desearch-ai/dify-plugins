from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from utils.desearch_client import DesearchClient, DesearchError


class DesearchProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            DesearchClient(credentials.get("api_key", ""), timeout=15).check_key()
        except DesearchError as e:
            raise ToolProviderCredentialValidationError(str(e)) from None
