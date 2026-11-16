# AI uninstaller prompt

Paste this into the AI harness you want to remove the filter from.

```text
Uninstall https://github.com/Zettersten/claude-prompt-expander from the harness running this chat. Detect Claude Code, OpenCode, or Pi from your runtime. Ask only if unclear. Uninstall from that one.

Never read, print, search, or inspect expand_abbreviations.py.

Use user config only. No sudo. No admin. Find the active config, including overrides. Back it up. Remove only entries that point into the claude-prompt-expander folder. Keep every other setting and JSONC comments. Remove a hook group or array only if it becomes empty.

- Claude Code: Remove the UserPromptSubmit and PostToolUse hooks whose commands run integrations/claude-code/check_prompt.py or integrations/claude-code/check_tool_output.py. Older installs may have only the first.
- OpenCode: Remove the integrations/opencode directory from user config plugins. The installer set settings.encoding to "none" for the active provider. Restore the earlier value if a backup shows it. Otherwise ask before changing it. Keep its URL and auth.
- Pi: Remove the integrations/pi/index.ts path from user settings.json extensions.

Validate the config after editing. Make no gateway calls. Then ask whether to delete the claude-prompt-expander folder. Delete it only on a clear yes. If you see entries for the other harnesses, list them and ask before removing them. Report what changed, what failed, and whether to restart.
```
