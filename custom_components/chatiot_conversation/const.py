"""Constants for the ChatIoT Conversation integration."""

DOMAIN = "chatiot_conversation"
INTEGRATION_VERSION = "2024.11.11"

CONF_PROVIDER = "provider"
CONF_API_KEY = "api_key"
CONF_BASE_URL = "base_url"
CONF_TEMPERATURE = "temperature"
CONF_MAX_TOKENS = "max_tokens"
CONF_ACCESS_TOKEN = "access_token"

PROVIDERS = [
    "qwen-max-latest",
    "deepseek-chat",
    "gpt-3.5-turbo-0125",
    "gpt-4-turbo",
    "gpt-4o"
]

DEFAULT_PROVIDER = PROVIDERS[0]
DEFAULT_API_KEY = "sk-f464e1e7f46e421ab0ccb290f505c66e"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024
DEFAULT_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI5YjViZWE5MGE1NWE0OGJiOTcwY2M2NmRkMDY2YWMzZiIsImlhdCI6MTczNjk4NzczNCwiZXhwIjoyMDUyMzQ3NzM0fQ.bxvglb2wsxAJ3vdD4L6l0SAGT8GiJz8WAW-wcP_CgEY"

DATA_PATH = "/config/.storage/chatiot_conversation"
WORK_PATH = "/config/custom_components/chatiot_conversation"