A mini cli agent.

Current ability:

- Run bash command
- Edit files
- Plan for complex tasks
- Run subagent
- Load skills

How to run this:

1. Use uv to sync dependencies `uv sync`
2. Configure OpenAI Completions/Responses API-compatible model providers in `providers.toml`
3. Run `uv run main.py`

> Known Limitation

Dashscope Responses API provided models may describe a next tool action without actually emitting the tool call during long tasks, causing the loop to stop early.

The same task may work correctly through the Chat Completions API, which suggests the issue can depend on the provider’s API compatibility layer and tool-calling implementation.
