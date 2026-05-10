Research the current state of all tools in `stack.toml` and produce `research_results.json`.

For each tool in `base_tools`, `mcp_servers`, and `per_project` sections:
1. Find the latest stable published version
2. Note any breaking changes since the pinned version (if pinned)
3. Note deprecation status: active, deprecated, or archived
4. Note any known security advisories
5. Note any relevant observations (renames, forks, maintenance concerns)

Output `research_results.json` with this exact structure:

```json
{
  "tools": [
    {
      "id": "tool_id_matching_stack_toml_key",
      "current_version": "x.y.z",
      "breaking_changes_since_pinned": [],
      "deprecation_status": "active",
      "security_advisories": [],
      "notes": ""
    }
  ]
}
```

Include ALL tools from all three sections. If the latest version cannot be determined, omit `current_version` for that tool. Do not guess versions.
