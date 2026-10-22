# Google Flow via useapi.net

This extension connects the hosted useapi.net Google Flow MCP server (`useapi-google-flow`, 12 tools). The tools chat with Google Flow Agent to make images and Veo 3.1 or Omni 1.1 Flash video, answer its credit approvals, manage chats and settings, list characters, voices and media, and upload images, on your Google AI subscription (a free account works too, Omni 1.1 Flash needs a paid one).

- Endpoint: https://api.useapi.net/v1/google-flow/mcp (Streamable HTTP), authorized with the user's useapi.net API token in `USEAPI_TOKEN`.
- Before the tools work, the user needs a useapi.net API token (https://useapi.net/docs/start-here/setup-useapi) and an account connected at https://useapi.net/docs/start-here/setup-google-flow.
- If a tool returns 401, ask the user to check `USEAPI_TOKEN` (`gemini extensions config useapi-google-flow`). If it says no account is configured, point them to the setup page above.
- Generations spend the Flow credits of the user's Google AI subscription. Ask before starting paid or long jobs, and report job status and links when they finish.
- Full tool list and limits: https://useapi.net/docs/api-google-flow-v1/mcp

The extension also ships the `omni-flash-video` agent skill from `skills/`, which calls the same API with curl and reads `USEAPI_TOKEN` from the environment.

useapi.net is a paid third-party API service ($15/month, covers every useapi.net API), not affiliated with Google.
