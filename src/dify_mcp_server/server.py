import asyncio
import json
import os
from abc import ABC

import mcp.server.stdio
import mcp.types as types
import requests
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from omegaconf import OmegaConf


def get_app_info():
    config_path = os.getenv("CONFIG_PATH")
    base_url = os.getenv("DIFY_BASE_URL")
    dify_app_sks = os.getenv("DIFY_APP_SKS")
    if config_path is not None:
        print(f"Loading config from {config_path}")
        config = OmegaConf.load(config_path)
        dify_base_url = config.get('dify_base_url', "https://api.dify.ai/v1")
        dify_app_sks = config.get('dify_app_sks', [])
        return dify_base_url, dify_app_sks
    elif base_url is not None and dify_app_sks is not None:
        print(f"Loading config from env variables")
        dify_base_url = base_url
        dify_app_sks = dify_app_sks.split(",")
        return dify_base_url, dify_app_sks

class DifyAPI(ABC):
    def __init__(self,
                 base_url: str,
                 dify_app_sks: list,
                 user="default_user"):
        # dify configs
        self.dify_base_url = base_url
        self.dify_app_sks = dify_app_sks
        self.user = user

        # dify app infos
        dify_app_infos = []
        dify_app_params = []
        dify_app_metas = []
        for key in self.dify_app_sks:
            dify_app_infos.append(self.get_app_info(key))
            dify_app_params.append(self.get_app_parameters(key))
            dify_app_metas.append(self.get_app_meta(key))
        self.dify_app_infos = dify_app_infos
        self.dify_app_params = dify_app_params
        self.dify_app_metas = dify_app_metas
        self.dify_app_names = [x['name'] for x in dify_app_infos]

    def chat_message(
            self,
            api_key,
            inputs={},
            response_mode="streaming",
            conversation_id=None,
            user="default_user",
            files=None,):
        url = f"{self.dify_base_url}/workflows/run"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user,
        }
        if conversation_id:
            data["conversation_id"] = conversation_id
        if files:
            files_data = []
            for file_info in files:
                file_path = file_info.get('path')
                transfer_method = file_info.get('transfer_method')
                if transfer_method == 'local_file':
                    files_data.append(('file', open(file_path, 'rb')))
                elif transfer_method == 'remote_url':
                    pass
            response = requests.post(
                url, headers=headers, data=data, files=files_data, stream=response_mode == "streaming")
        else:
            response = requests.post(
                url, headers=headers, json=data, stream=response_mode == "streaming")
        response.raise_for_status()
        if response_mode == "streaming":
            for line in response.iter_lines():
                if line:
                    if line.startswith(b'data:'):
                        try:
                            json_data = json.loads(line[5:].decode('utf-8'))
                            yield json_data
                        except json.JSONDecodeError:
                            print(f"Error decoding JSON: {line}")
        else:
            return response.json()

    def upload_file(
            self,
            api_key,
            file_path,
            user="default_user"):

        url = f"{self.dify_base_url}/files/upload"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        files = {
            "file": open(file_path, "rb")
        }
        data = {
            "user": user
        }
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()

    def stop_response(
            self,
            api_key,
            task_id,
            user="default_user"):

        url = f"{self.dify_base_url}/chat-messages/{task_id}/stop"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "user": user
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_app_info(
            self,
            api_key,
            user="default_user"):

        url = f"{self.dify_base_url}/info"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        params = {
            "user": user
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_app_parameters(
            self,
            api_key,
            user="default_user"):
        url = f"{self.dify_base_url}/parameters"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        params = {
            "user": user
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_app_meta(
            self,
            api_key,
            user="default_user"):
        url = f"{self.dify_base_url}/meta"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        params = {
            "user": user
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


base_url, dify_app_sks = get_app_info()
server = Server("dify_mcp_server")
dify_api = DifyAPI(base_url, dify_app_sks)


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    tools = []
    tool_names = dify_api.dify_app_names
    tool_infos = dify_api.dify_app_infos
    tool_params = dify_api.dify_app_params
    tool_num = len(tool_names)
    for i in range(tool_num):
        # 0. load app info for each tool
        app_info = tool_infos[i]
        # 1. load app param for each tool
        inputSchema = dict(
            type="object",
            properties={},
            required=[],
        )
        app_param = tool_params[i]
        property_num = len(app_param['user_input_form'])
        if property_num > 0:
            for j in range(property_num):
                param = app_param['user_input_form'][j]
                # TODO: Add readme about strange dify user input param format
                param_type = list(param.keys())[0]
                param_info = param[param_type]
                property_name = param_info['variable']
                inputSchema["properties"][property_name] = dict(
                    type=param_type,
                    description=param_info['label'],
                )
                if param_info['required']:
                    inputSchema['required'].append(property_name)

        tools.append(
            types.Tool(
                name=app_info['name'],
                description=app_info['description'],
                inputSchema=inputSchema,
            )
        )
    return tools


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    tool_names = dify_api.dify_app_names
    if name in tool_names:
        tool_idx = tool_names.index(name)
        tool_sk = dify_api.dify_app_sks[tool_idx]
        responses = dify_api.chat_message(
            tool_sk,
            arguments,
        )
        for res in responses:
            if res['event'] == 'workflow_finished':
                outputs = res['data']['outputs']
        mcp_out = []
        for _, v in outputs.items():
            mcp_out.append(
                types.TextContent(
                    type='text',
                    text=v
                )
            )
        return mcp_out
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="dify_mcp_server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
