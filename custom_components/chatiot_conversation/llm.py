from configs import CONFIG
from utils.logs import _logger
from utils.singleton import Singleton
from typing import NamedTuple
from openai import OpenAI
from tenacity import retry, stop_after_attempt
import httpx

# prices = {
#     "gpt-4-turbo": (10, 30),
#     "gpt-4o": (5, 15),
#     "gpt-3.5-turbo": (0.5, 1.5),
#     "deepseek-chat": (0.14, 0.28),
#     "deepseek-reasoner": (0.14, 0.28),
#     "qwen-max-latest": (0.002, 0.006),
# }

class Costs(NamedTuple):
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost: float

class CostManager(metaclass=Singleton):
    def __init__(self):
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost = 0.0

    def update_cost(self, completion_tokens, prompt_tokens, cost):
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_cost += cost
        CONFIG.total_cost = self.total_cost

    def get_total_prompt_tokens(self):
        return self.total_prompt_tokens
    
    def get_total_completion_tokens(self):
        return self.total_completion_tokens
    
    def get_total_cost(self):
        return self.total_cost
    
    @property
    def costs(self):
        return Costs(self.total_prompt_tokens, self.total_completion_tokens, self.total_cost)
    
class LLM():
    def __init__(self):
        self._cost_manager = CostManager()
        self.total_completion_tokens = 0
        self.total_prompt_tokens = 0
        self.total_cost = 0.0
        self.model = CONFIG.configs_llm["provider"]
        self.temperature = CONFIG.configs_llm["temperature"]
        self.max_tokens = int(CONFIG.configs_llm["max_tokens"])
        self._init_client()
        self.history = []
        _logger.debug(f"configs_llm: {CONFIG.configs_llm}")

    def add_system_msg(self, msg):
        self.history.append({"role": "system", "content": msg})

    def add_user_msg(self, msg):
        self.history.append({"role": "user", "content": msg})

    def add_assistant_msg(self, msg):
        self.history.append({"role": "assistant", "content": msg})

    def _init_client(self):
        self.client = OpenAI(
            base_url = CONFIG.configs_llm["base_url"],
            api_key = CONFIG.configs_llm["api_key"],
            http_client = httpx.Client(
                base_url = CONFIG.configs_llm["base_url"],
                follow_redirects = True
            )
        )

    @retry(stop=stop_after_attempt(6))
    def chat_completion_json_v1(self, messages: list[dict]) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format= {"type": 'json_object'},
        )
        _logger.debug(f"response: {response}")
        rsp = response.choices[0].message.content
        usage = response.usage
        completion_tokens = usage.completion_tokens
        prompt_tokens = usage.prompt_tokens
        # cost = round((completion_tokens * prices[self.model][0] + prompt_tokens * prices[self.model][1]) * 7.15 / 1e6, 6)
        cost = 0.0
        self._cost_manager.update_cost(completion_tokens, prompt_tokens, cost)
        self._update_llm_cost(completion_tokens, prompt_tokens, cost)
        return rsp

    @retry(stop=stop_after_attempt(6))
    def chat_completion_text_v1(self, messages: list[dict]) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        _logger.debug(f"response: {response}")
        rsp = response.choices[0].message.content
        usage = response.usage
        completion_tokens = usage.completion_tokens
        prompt_tokens = usage.prompt_tokens
        # cost = round((completion_tokens * prices[self.model][0] + prompt_tokens * prices[self.model][1]) * 7.15 / 1e6, 6)
        cost = 0.0
        self._cost_manager.update_cost(completion_tokens, prompt_tokens, cost)
        self._update_llm_cost(completion_tokens, prompt_tokens, cost)
        return rsp
    
    def _update_llm_cost(self, completion_tokens, prompt_tokens, cost):
        self.total_completion_tokens += completion_tokens
        self.total_prompt_tokens += prompt_tokens
        self.total_cost += cost

    def reset(self):
        self.history = []
        self.total_completion_tokens = 0
        self.total_prompt_tokens = 0
        self.total_cost = 0.0
        self.model = CONFIG.configs_llm["provider"]

if __name__ == "__main__":
    # CONFIG.configs_llm = {
    #     "provider": "qwen-max-latest",
    #     "temperature": 0.7,
    #     "max_tokens": 1024,
    #     "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    #     "api_key": "sk-f464e1e7f46e421ab0ccb290f505c66e"
    # }
    CONFIG.configs_llm = {
        "provider": "deepseek-chat",
        "api_key": "sk-3409f67c5ec841a4b5e5e9b3d0bb3417",
        "base_url": "https://api.deepseek.com",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    llm = LLM()
    llm.add_user_msg("Hello")
    print(llm.chat_completion_text_v1(llm.history))
    print(llm._cost_manager.costs)