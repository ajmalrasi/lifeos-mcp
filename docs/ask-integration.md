# Reusing these tools in LifeOS Ask

Yes: ChatGPT, Hermes and Ask can consume the same MCP server interface. Keep
health aggregation, spending exclusions, reconciliation, currencies and date
logic in LifeOS services; the MCP project owns tool schemas and transport.

The initial repository does not switch Ask to MCP. Today Ask still calls its
existing internal functions. The optional adapter also calls those same functions,
so adding Hermes need not create a second calculation implementation.

Suggested later migration:

1. Deploy and evaluate the connector against LifeOS's current tool outputs.
2. Add a bounded MCP client to Ask with startup discovery, cached schemas and
   explicit allowed tool names. Translate MCP JSON schemas into the local model's
   existing function-calling format; omit transport-only annotations there.
3. Replace selected internal dispatches with MCP calls. Keep personal retrieval
   optional and model-selected. Do not prefetch all data or introduce canned
   answers when a tool/model fails.
4. Carry sources and tool errors into the current citation/status system; strip
   large metadata before sending results to the 6144-input-token local engine.
5. Run `backend/scripts/evaluate_ask.py` and inspect actual arithmetic, dates,
   EMI rules, citations and outage behavior before replacing the existing path.

Use one authoritative schema per migrated tool. The current optional tools accept
`{"query": {...}}`; existing Ask's corresponding tools use flat arguments. The
migration must adapt those arguments intentionally rather than assuming they are
drop-in replacements. Existing health windows remain limited to 90 days.

Ask can launch a local stdio subprocess with the server extra in a separate virtual
environment. That avoids upgrading the backend's pinned dependencies and avoids a
dependency on the Pi for every Ask request. A future authenticated HTTP MCP service
could serve multiple clients, but it is not part of v0.2. See `clients.md` for the
ChatGPT Secure MCP Tunnel path to the existing stdio server. The 38-tool catalog
need not be injected into Ask's small context all at once; discovery and selection
should preserve its existing token budget.

Do not route tools through `/chat`: that adds a second model invocation and can
create a recursion loop when Ask itself is the caller. Tool results must remain
structured data produced by LifeOS, with no model-written factual fallback.
