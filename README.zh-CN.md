# EchoAlly Skill

[English](README.md)

在外部 AI 中读取 EchoAlly 的记录卡片、待办、已保存发言人和个人简报，将讨论结果保存为备忘或待办。每个连接可使用的工具由其授权范围决定。

## 连接账号

在 EchoAlly App 的 AI 连接页创建密钥并复制当前环境的 MCP 地址。默认地址为 `https://dev.ichunzhen.cn/mcp`。选择 OAuth 后，仅在 **EchoAlly 自己的网页** 输入密钥，勾选需要的权限。请勿在聊天、命令或仓库中粘贴密钥。App 支持按客户端断开 OAuth 授权。轮换密钥也会让基于旧密钥的连接失效。 如果之前连接过旧域名，请改用新地址并重新授权。

| 使用端 | 安装与连接 |
| --- | --- |
| Claude Code | 依次执行 `/plugin marketplace add iChunzhen/echoally-skill`、`/plugin install echoally@echoally-skills`。插件已配置默认 MCP，打开 `/mcp` 完成授权。 |
| Codex | 用 Skill 安装器安装本仓库的 `skills/echoally`。执行 `codex mcp add echoally --url https://dev.ichunzhen.cn/mcp`，按提示完成授权。需要重新登录时执行 `codex mcp login echoally`。 |
| WorkBuddy | 在「技能 → 添加技能 → 上传技能」导入下方的技能 ZIP。可在支持的工作区添加 Streamable HTTP 连接器，填 App 提供的 URL 并使用个人 OAuth，也可使用本地调用方式。[腾讯云安装说明](https://www.tencentcloud.com/document/product/1316/84503) |
| 豆包工作 | 在工作模式启动任务，通过「插件·技能·伙伴」导入本地技能，或让工作模式安装本仓库的 `skills/echoally`。使用工作区已有的远程连接器或配置下方的本地调用方式，再新建任务启用。[火山引擎工作模式说明](https://docs.volcengine.com/docs/agent-toolkit/agent-auto-install-guide?lang=zh) |
| ChatGPT | 网页端打开 Plugins，在加号菜单选择 Add custom MCP server，填写 App 地址，选择 OAuth 并授权。可用范围取决于工作区设置。[OpenAI 接入说明](https://developers.openai.com/plugins/deploy/connect-chatgpt) |
| Claude | 在 Customize → Connectors 添加自定义 Web 连接器，填写 App 地址，选择 OAuth 自动注册并连接。受管理的组织可由管理员先添加连接器。[Claude 接入说明](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp) |

可执行安装任务的桌面 AI 也可以从这句话开始：

> 请从 https://github.com/iChunzhen/echoally-skill 安装 skills/echoally，连接我的 EchoAlly 账户，并列出当前可用工具。

如果 App 展示其他环境地址，请在命令中替换 URL。Claude Code 使用自定义环境时，将技能目录复制到 `~/.claude/skills/`，再用 `claude mcp add --transport http --scope user echoally <APP_MCP_URL>` 添加该环境。Codex 如需为只读授权新增待办写权限，可按需申请，例如 `codex mcp login echoally --scopes todos:read,todos:write`。

## 本地技能包和密钥

在仓库根目录执行 `git archive --format=zip --prefix=echoally/ HEAD:skills/echoally -o echoally.zip`，即可生成上述 ZIP。支持本地目录的客户端也可直接导入完整的 `skills/echoally`。

对于支持执行 Python 3 的本地桌面技能，在宿主的私密环境变量或凭据管理器内配置 `ECHOALLY_API_KEY`，再启动新任务。此密钥拥有本账号的全部工具权限。其他部署使用 `ECHOALLY_MCP_URL` 指定 App 显示的 HTTPS 地址。在已安装的技能目录执行 `python3 scripts/echoally.py list` 验证连接。Codex 原生 MCP 也支持通过环境变量获取密钥，使用 `codex mcp add echoally --url https://dev.ichunzhen.cn/mcp --bearer-token-env-var ECHOALLY_API_KEY` 配置。

## 验证

先试「列出我最近三张 EchoAlly 记录卡片」，再试「把刚才的结论保存为 EchoAlly 备忘，告诉我保存后的 ID」。本地测试命令为 `python3 -m unittest discover -s tests -v`，使用临时 HTTPS 服务和测试密钥，需要系统可执行 `openssl`。
