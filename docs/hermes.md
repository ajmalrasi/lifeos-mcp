# Hermes on the Raspberry Pi

These are installation instructions, not a record of deployment. No Hermes
configuration has been changed by creating this repository.

Install the repository under `/home/ajmalrasi/apps/lifeos-mcp` in its own virtual
environment using `pip install '.[server]'`. This does not require a background
service: Hermes launches the MCP process on demand.

Merge the following entry into `~/.hermes/config.yaml`, preserving other entries:

```yaml
mcp_servers:
  lifeos:
    command: /home/ajmalrasi/apps/lifeos-mcp/.venv/bin/lifeos-mcp
    env:
      LIFEOS_API_BASE_URL: http://192.168.3.30:8000
    timeout: 30
    connect_timeout: 15
```

If backend authentication is enabled, store `LIFEOS_API_TOKEN` in Hermes's private
secret environment, then add `LIFEOS_API_TOKEN: "${LIFEOS_API_TOKEN}"` under this
entry's `env`. Never paste the token into chat or the repository. A token is not
needed solely because this connector exists; follow the actual backend settings.

The server advertises all 40 standard read tools. No adapter flag or second token
is needed. Remove or expand any old 12-tool include list, then use `/reload-mcp`.
Native health and money routes must be present in LifeOS before making those reads.

Acceptance checks after deployment:

1. Discover 40 tools.
2. Ask when health and Money last synced; compare with LifeOS source status.
3. Ask for card bills and compare IDs, amounts and due dates with LifeOS.
4. Compare exact money dates and health windows with
   existing Ask tool results. State EMI inclusion before comparing totals.
5. Confirm API outages yield errors, not empty lists or invented summaries.

The connector calls the Jetson directly, not the Pi web proxy. Remote Hermes
deployment would need private network connectivity to the same backend.

Official reference: https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference
