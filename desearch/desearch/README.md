# Desearch

Search the web, search X (Twitter) and get AI answers with links to their sources, inside Dify workflows, chatflows and agents.

## Tools
- **Web Search**: titles, links and snippets for a query.
- **AI Search**: an AI answer with links to its sources from web, X, Reddit, Hacker News, arXiv and Wikipedia.
- **X Search**: X posts that match a query, with optional filters for user, language, date range and sort order.

## Setup
1. Create a Desearch API key: https://console.desearch.ai/api-keys
2. Install the Desearch plugin from the Dify Marketplace.
3. Open the plugin, choose Authorize, and paste your API key. Dify checks the key without running a search, so the check is not billed.
4. Add a Desearch tool to a workflow, chatflow or agent.

## Requirements
- A Desearch API key. Desearch is pay as you go, billed per API by usage: https://desearch.ai/pricing
- Network connection: your Dify instance needs outbound HTTPS access to the Desearch API endpoint, api.desearch.ai.

## Compatibility
Tested on Dify Community Edition 1.17.1.

## Privacy
See [PRIVACY.md](./PRIVACY.md).

## Source and contact
- Source: https://github.com/Desearch-ai/dify-plugin-desearch
- Docs: https://www.desearch.ai/docs
- Contact: dev@desearch.ai

## License

MIT License. See [LICENSE](LICENSE).
