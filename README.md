# Prompt Abbreviation Expander

A dependency-free Python filter with integrations for Claude Code, OpenCode, and Pi. The hook blocks a submitted prompt when it finds a configured abbreviation and shows the expanded text to resubmit.

## Install with an AI assistant

Copy the [AI installer prompt](INSTALL-PROMPT.md), specify Claude Code, OpenCode, or Pi, and give it to your assistant. The prompt directs the assistant to install the selected integration and merge the user config using absolute paths.

## Claude Code

1. Install Python 3 and confirm `python3 --version` works in the terminal where you run Claude Code. The Claude hook can use `py -3` on Windows if that is your Python launcher. The provider adapters currently expect `python3` on PATH.
2. Clone this repository or use **Code → Download ZIP** and extract it to a stable location.
3. Merge [the settings example](integrations/claude-code/settings.json) into `~/.claude/settings.json` (Windows: `%USERPROFILE%\.claude\settings.json`). Replace the example path with the absolute path to `check_prompt.py`. Keep the downloaded directory structure intact. If you already have a `UserPromptSubmit` array, append the entry. On Windows, use forward slashes in the path or escape backslashes for JSON.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"/absolute/path/to/claude-prompt-expander/integrations/claude-code/check_prompt.py\""
          }
        ]
      }
    ]
  }
}
```

4. Restart Claude Code. Submit `Review the eIcD.` The hook should block it and show `Review the External Interface Control Document.` Submit the expanded prompt to proceed.

## OpenCode

Use a version with the server plugin API and the `http.request` hook. Add the
absolute path to the downloaded `integrations/opencode` directory to the
`plugins` array in your OpenCode config. Keep your provider URL and credentials.
Set your provider's `settings.encoding` to `"none"`. This plugin processes
JSON request bodies for providers routed through the session HTTP hook.

## Pi

Launch with `pi -e /absolute/path/to/claude-prompt-expander/integrations/pi/index.ts`.
For persistent loading, add that absolute path to the `extensions` array in
`~/.pi/agent/settings.json`. Use a Pi build that exposes
`before_provider_request`. The extension replaces the provider payload before
sending.

For both clients, verify against a mock endpoint before rollout. Check a prompt
and a tool result, then temporarily make Python unavailable and verify that no
unfiltered request reaches the endpoint. Hook behavior on errors and request
coverage depend on the installed version and provider.

## Customize the terms

Edit `ABBREVIATIONS` in `expand_abbreviations.py`. Keep keys lowercase and use plain ASCII letters and digits. Matching is case-insensitive and works inside words, so `dow` also matches inside `download`. Use expansions that contain none of your configured abbreviations so the expanded prompt can pass on resubmission.

Run the raw text filter independently:

```sh
printf '%s\n' 'Review the eIcD.' | python3 expand_abbreviations.py
```

## Scope

The hook checks submitted user prompts. Claude Code controls hook execution and can continue after certain hook execution errors. Files, tool results, instructions, and conversation history can also contribute text outside this hook. This is a prompt guard, not a guarantee about the complete gateway payload.

To uninstall, remove the hook entry from your user settings.

[Claude Code hooks reference](https://code.claude.com/docs/en/hooks#userpromptsubmit)
