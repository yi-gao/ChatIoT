from actions.action import Action
from message import Message
from utils.logs import _logger
from llm import LLM
import asyncio
from string import Template

SYSTEM_MESSAGE = '''
# Role
You are a useful assistant named Manager in smart home. There are several assistants can help user to do some tasks. If user's request can be done by one of the assistants, you should assign the user's request to the corresponding assistant for execution. Otherwise, you should tell the user that you can't understand the request and tell user what the assistants can do for the user now.

# Input
1. Assistant list: The list of the assistants in the smart home now.
2. User request: The user's request.

# Workflow
1. Understand the user's request.
2. Assign the user's request to the corresponding assistant for execution or tell the user that you can't understand the request and tell user what the assistants can do for the user.

# Output
Your output should AlWAYS in the following format:
${format_example}
'''

INIT_USER_MESSAGE = '''
---Assistant list---
${assistant_list}
---User request---
${user_request}
'''

FORMAT_EXAMPLE = '''
---
1. If user's request can be done by one of the assistants, your output should be the name of the assistant.
2. If user request can't be done by any assistant, your output should be "Sorry, I can't process your request currently." and tell user what the assistants can do for the user without mentioning the assistants' details. In this case, your output must in the same language as the user's request.

# Examples
If the assistant list is as follows:
1. DeviceControler
description: help user to control the devices in the smart home at one time.
examples: "Turn on the light.", "Turn on the air conditioner in heating mode and set the temperature to 25 degrees."
2. TapGenerator
description: help user to generate a home automation which is triggered by time or device status and control the devices or scenes in the smart home.
examples: "turn on the light when I come back home.", "turn on the air conditioner when the temperature is higher than 30 degrees."
Then given the following user requests:
Case 1: "Turn on the light.", your output should be "DeviceControler".
Case 2: "回家自动开灯", your output should be "TapGenerator".
Case 3: "帮我删除一条场景或自动化", your output should be "抱歉，我现在无法处理您的这个请求。您可以尝试以下操作：1.控制设备（如打开灯）；2.创建自动化（如回家自动开灯）。"
---
'''

OUTPUT_MAPPING = {}

class Router(Action):
    def __init__(self, name="Manager", context=None):
        super().__init__(name, context)
        self.llm = LLM()

    async def run(self, history_msg: list[Message], user_input: Message) -> Message:
        user_request = user_input.content
        SYSTEM_MESSAGE_Template = Template(SYSTEM_MESSAGE)
        self.llm.add_system_msg(SYSTEM_MESSAGE_Template.substitute(format_example=FORMAT_EXAMPLE))
        USER_MESSAGE_Template = Template(INIT_USER_MESSAGE)
        assistant_list = '''
1. DeviceControler
description: help user to control the devices in the smart home at one time.
examples: "Turn on the light.", "Turn on the air conditioner in heating mode and set the temperature to 25 degrees."
2. TapGenerator
description: help user to generate a home automation which is triggered by time or device status and control the devices or scenes in the smart home.
examples: "turn on the light when I come back home.", "turn on the air conditioner when the temperature is higher than 30 degrees."
'''
        self.llm.add_user_msg(USER_MESSAGE_Template.substitute(assistant_list=assistant_list, user_request=user_request))
        loop = asyncio.get_running_loop()
        rsp = await loop.run_in_executor(None, self.llm.chat_completion_text_v1, self.llm.history)
        _logger.info(f"Router response: {rsp}")
        self.llm.reset()
        if rsp == "DeviceControler":
            return Message(role=self.name, content=user_request, send_to=["DeviceControler"], sent_from="Manager", cause_by="UserInput")
        elif rsp == "TapGenerator":
            return Message(role=self.name, content=user_request, send_to=["TapGenerator"],  sent_from="Manager",cause_by="UserInput")
        else:
            return Message(role=self.name, content=rsp, send_to=["User"], cause_by="Finish", sent_from="Manager")