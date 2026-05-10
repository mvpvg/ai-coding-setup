Research the tool at the provided URL and draft a `stack.toml` entry.

Steps:
1. Identify: tool name, source type (npm / pypi / github / marketplace / official), package or repo
2. Find the latest stable version
3. Check for known security issues or maintenance concerns
4. Determine section: `base_tools` (always installed), `mcp_servers` (MCP protocol), or `per_project` (trigger-based)

Draft the TOML entry. Examples:

```toml
# base_tools or mcp_servers
[base_tools]
my_tool = { source = "npm", package = "@scope/package", pinned_version = "x.y.z" }

# per_project (trigger: "has_e2e_tests" | "manual")
[per_project]
my_tool = { trigger = "manual", source = "pypi", package = "my-package", pinned_version = "x.y.z" }
```

Present the draft entry and explain the rationale. Ask for confirmation before appending to `stack.toml`. If confirmed, append the entry to the correct section and run:

```bash
python scripts/update_stack.py --stack stack.toml generate
```

to regenerate `STACK.md` and `MANIFEST.json`.
