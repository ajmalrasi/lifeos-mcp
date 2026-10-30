# One LifeOS server, multiple MCP clients

LifeOS MCP is client-neutral. Hermes is one integration example. The server code
contains no Hermes-specific dispatch or model/provider dependency.

| Client | Connection path | Current state |
|---|---|---|
| Local compatible MCP host, including Hermes | Launch `lifeos-mcp` as a stdio subprocess | Implemented and protocol-tested; not configured in production |
| ChatGPT custom MCP connection | Secure MCP Tunnel forwarding to this stdio server | Documented path; no tunnel, credentials or ChatGPT connection created |
| ChatGPT through a direct server URL | Authenticated remote MCP transport | Would require adding and hosting an HTTP MCP service; not implemented here |
| LifeOS Ask | An MCP client over the same catalog | Future migration; Ask currently retains its existing tool dispatch |

## ChatGPT

ChatGPT supports custom MCP servers, subject to workspace permissions. Its setup
accepts a server URL or a Secure MCP Tunnel. A tunnel client can forward requests
to a private stdio server, so this package can be used without publishing the
Jetson API. The tunnel requires setup and credentials and must remain running;
this repository has not configured it or checked your account's access.

When connecting later, run the tunnel client on a machine that can reach the
Jetson, configure it to launch the installed `lifeos-mcp` executable, then select
that tunnel in ChatGPT's custom MCP setup. Verify discovery and a representative
read before calling the connection complete.

Official references, checked 2026-10-31:

- [Add a custom MCP server](https://developers.openai.com/api/docs/guides/custom-mcp-server)
- [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels)

The catalog contains the same 40 standard tools across clients. Rendering an attachment resource and
displaying large tool responses depend on the host. Retrieved health, money,
email and trip information enters the client's conversation and may be retained
or sent to its configured model provider. Read-only access prevents tool-mediated
edits; it does not prevent disclosure of the data you ask a client to retrieve.
