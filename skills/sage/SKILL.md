---
name: sage
description: Open SAGE controls inside the current harness to list or select an OpenCode assistant model and turn hybrid delegation on or off. Use for /sage and explicit fleet setting requests.
---

# SAGE controls

Use the connected Hybrid SAGE MCP `configure_fleet` tool directly. Do not run a
terminal command, start a worker, or edit configuration files to perform these
controls. If the tool is unavailable, report the missing connection.

Interpret the text following `/sage` (or `$sage`) as a control request:

| Request | Tool arguments |
| --- | --- |
| Empty, `help`, or `status` | `action="status"` |
| `models` | `action="list", provider="opencode", limit=20` |
| `models <provider>` | `action="list", provider=<provider>, limit=20` |
| `model <provider/model>` | `action="select", model_id=<exact ID>` |
| `model <provider/model> --allow-paid` | Same selection with `allow_paid=true` |
| `on` or `hybrid on` | `action="enable"` |
| `off` or `hybrid off` | `action="disable"` |

For bare `/sage`, show the actual enabled state, current assistant model, and cost
policy, followed by the short choices Models / Select model / On / Off. Ask for
an exact model ID only when selection was requested without one. List catalog
entries with their advertised price status and use `next_offset` for more pages,
preserving the provider filter. Catalog membership does not prove live availability.

Honor clear equivalent natural-language requests. Unknown commands show help and
do not mutate settings. Use structured tool arguments; never evaluate request text
as code. A paid or unknown-price selection requires the user's explicit paid opt-in;
do not infer it from a request merely to view or select a model.

Report the persisted result returned by the tool, including any error. Selecting
a model does not enable hybrid mode. Off stops new delegation and consultations;
it does not cancel existing jobs. On retains the selected model. Never re-enable
hybrid mode without the user's request. These are assistant settings, not changes
to the frontier model running the conversation.
