# EchoAlly Skill

[中文安装说明](README.zh-CN.md)

Connect your AI assistant to your EchoAlly account to read record cards, saved speakers, to-dos and personal context. Save an AI-generated conclusion as a memo or turn a decision into a to-do. The hosted service advertises the tools allowed by your connection.

## Connect

Open AI connections in the EchoAlly App and create a key. Use the **MCP URL shown in the App** for your deployment. The default is `https://echoally.ichunzhen.cn/mcp`. For OAuth connections, enter the key on the **EchoAlly authorization page** and select the permissions you want. Keep your key out of chats, commands and Git. Disconnect an OAuth client individually in the App. Rotating the App key also invalidates connections authorized by that key.

| Client | Installation |
| --- | --- |
| Codex | Install `skills/echoally` from this repository with the skill installer. Run `codex mcp add echoally --url https://echoally.ichunzhen.cn/mcp` then `codex mcp login echoally` if prompted. |
| Claude Code | Run `/plugin marketplace add EchoElly/echoally-skill` then `/plugin install echoally@echoally-skills`. The plugin includes the default remote MCP URL. Open `/mcp` to authenticate. |
| WorkBuddy | Open Skills → Add skill → Upload skill and import the skill ZIP described below. Use your workspace's custom Streamable HTTP connector with the App URL and per-user OAuth where available, or configure the local runner. [Tencent skill guide](https://www.tencentcloud.com/document/product/1316/84503) |
| Doubao Work | Start a Work task and import the local skill under 插件·技能·伙伴, or have Work mode install the `skills/echoally` folder. Use an available remote connector or configure the local runner. Start a new task after installation. [Local skills guide](https://docs.volcengine.com/docs/agent-toolkit/agent-auto-install-guide?lang=zh) |
| ChatGPT | On the web choose Plugins → + → Add custom MCP server. Enter the App URL, select OAuth and finish connecting. Workspace policy controls availability. [OpenAI guide](https://developers.openai.com/plugins/deploy/connect-chatgpt) |
| Claude | Choose Customize → Connectors → Add a custom web connector and enter the App URL. Choose OAuth auto-registration if offered, then Connect. In managed workspaces an admin may need to add the connector first. [Claude guide](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp) |

For a different deployment in Claude Code, install the skill folder under `~/.claude/skills/` and register its endpoint with `claude mcp add --transport http --scope user echoally <APP_MCP_URL>` instead of installing the bundled plugin. Use the same URL substitution for Codex. To request write access on a read-only Codex OAuth grant, reauthorize with the scopes you need, for example `codex mcp login echoally --scopes todos:read,todos:write`.

For a GitHub-capable desktop assistant, a single installation request is sufficient to start setup:

> Install skills/echoally from https://github.com/EchoElly/echoally-skill, connect it to my EchoAlly account and show the available tools.

## Local skill package and private key configuration

From the repository root, run `git archive --format=zip --prefix=echoally/ HEAD:skills/echoally -o echoally.zip` and import that ZIP where the host supports local skill packages. It includes the optional Python 3 runner for desktop hosts with command execution. It can also be installed by copying the entire `skills/echoally` directory into the host's skill directory.

For the runner, configure `ECHOALLY_API_KEY` privately in the host's environment or secret manager before starting a task. A key grants all tools for its owner. For another deployment, set `ECHOALLY_MCP_URL` to the HTTPS URL displayed by that App. The runner never follows redirects. From the installed skill folder run `python3 scripts/echoally.py list` to verify the connection. In a native Codex setup you can select key authentication directly with `codex mcp add echoally --url https://echoally.ichunzhen.cn/mcp --bearer-token-env-var ECHOALLY_API_KEY`.

## Try it

- “Show my three most recent EchoAlly record cards, with their titles.”
- “Use the records and open to-dos I shared to prepare a brief for today's project meeting.”
- “Save that conclusion to EchoAlly as a memo and give me its ID.”

Run the local runner tests with `python3 -m unittest discover -s tests -v` (requires OpenSSL on PATH). Tests use a temporary HTTPS server and a dummy key.
