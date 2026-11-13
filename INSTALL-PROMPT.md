# AI installer prompt

Paste this into the AI harness you want to set up.

```text
Install https://github.com/Zettersten/claude-prompt-expander for the harness running this chat. Detect Claude Code, OpenCode, or Pi from your runtime. Ask only if unclear. Install one.

Clone or download into a stable folder owned by the user. Keep the folder tree. Never read, print, search, or inspect expand_abbreviations.py. Let the hook run it locally.

Use user config only. No sudo. No admin. Find the active config, including overrides. Back it up. Merge with absolute paths. Keep existing settings and JSONC comments. Add no duplicates.

- Claude Code: Merge integrations/claude-code/settings.json into user settings.json. Set the command to the available Python 3 launcher and the quoted absolute path to integrations/claude-code/check_prompt.py.
- OpenCode: Add the absolute integrations/opencode directory to user config plugins. Set settings.encoding to "none" for the active provider. Keep its URL and auth.
- Pi: Add the absolute integrations/pi/index.ts path to user settings.json extensions.

Check Python and hook support first. OpenCode and Pi need python3 on PATH. Validate config and paths. Test locally if possible. Make no gateway calls. Report what changed, what failed, and whether to restart.
```
