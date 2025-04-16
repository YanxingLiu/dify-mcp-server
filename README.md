# Model Context Protocol (MCP) Server for dify workflows
A simple implementation of an MCP server for using [dify](https://github.com/langgenius/dify). It achieves the invocation of the Dify workflow by calling the tools of MCP.
## 📰 News
* [2025/4/15] zNow supports directly using environment variables to pass `base_url` and `app_sks`, making it more convenient to use with cloud-hosted platforms.


## 🔨Installation
The server can be installed via [Smithery](https://smithery.ai/server/dify-mcp-server) or manually. 

### Step1: prepare config.yaml or enviroments

#### Env
You can also use env viriables to supply dify_base_url and dify_app_sks
```shell
DIFY_BASE_URL="https://cloud.dify.ai/v1"
DIFY_BASE_SKS="app-sk1,app-sk2"
```
Different SKs correspond to different dify workflows.
#### Config.yaml
Before using the mcp server, you should prepare a config.yaml to save your dify_base_url and dify_sks. The example config like this:
```yaml
dify_base_url: "https://cloud.dify.ai/v1"
dify_app_sks:
  - "app-sk1"
  - "app-sk2"
```
You can run the following command in your terminal to quickly create a configuration file:
```
mkdir -p ~/tools && cat > ~/tools/config.yaml <<EOF
dify_base_url: "https://cloud.dify.ai/v1"
dify_app_sks:
  - "app-sk1"
  - "app-sk2"
EOF
```
Different SKs correspond to different dify workflows.

### Step2: Installation on your client
❓ If you haven't installed uv or uvx yet, you can do it quickly with the following command:
```
curl -Ls https://astral.sh/uv/install.sh | sh
```

#### ✅ Method 1: Use uvx (no need to clone code, recommended)

```json
"mcpServers": {
  "dify-mcp-server": {
    "command": "uvx",
      "args": [
        "--from","git+https://github.com/YanxingLiu/dify-mcp-server","dify_mcp_server"
      ],
    "env": {
       "CONFIG_PATH": "/Users/lyx/Downloads/config.yaml"
    }
  }
}
```
or
```json
"mcpServers": {
  "dify-mcp-server": {
    "command": "uvx",
      "args": [
        "--from","git+https://github.com/YanxingLiu/dify-mcp-server","dify_mcp_server"
      ],
    "env": {
       "DIFY_BASE_URL": "https://cloud.dify.ai/v1",
       "DIFY_APP_SKS": "app-sk1,app-sk2",
    }
  }
}
```

#### ✅ Method 2: Use uv (local clone + uv start)

You can also run the dify mcp server manually in your clients. The config of client should like the following format:
```json
{
"mcpServers": {
  "mcp-server-rag-web-browser": {
    "command": "uv",
      "args": [
        "--directory", "${DIFY_MCP_SERVER_PATH}",
        "run", "dify_mcp_server"
      ],
    "env": {
       "CONFIG_PATH": "$CONFIG_PATH"
    }
  }
}
}
```
or 
```json
{
"mcpServers": {
  "mcp-server-rag-web-browser": {
    "command": "uv",
      "args": [
        "--directory", "${DIFY_MCP_SERVER_PATH}",
        "run", "dify_mcp_server"
      ],
    "env": {
       "CONFIG_PATH": "$CONFIG_PATH"
    }
  }
}
}
```
Example config:
```json
{
"mcpServers": {
  "dify-mcp-server": {
    "command": "uv",
      "args": [
        "--directory", "/Users/lyx/Downloads/dify-mcp-server",
        "run", "dify_mcp_server"
      ],
    "env": {
       "DIFY_BASE_URL": "https://cloud.dify.ai/v1",
       "DIFY_APP_SKS": "app-sk1,app-sk2",
    }
  }
}
}
```
### Enjoy it
At last, you can use dify tools in any client who supports mcp.
