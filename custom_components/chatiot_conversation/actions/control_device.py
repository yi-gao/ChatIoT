from actions.action import Action
from configs import CONFIG
from message import Message
from utils.logs import _logger
from llm import LLM
import json
from translator import Translator
import asyncio
from string import Template

SYSTEM_MESSAGE = '''
# Role
You are a useful assistant named ChatIoT in the field of smart home. Your task is to parse user input into Commands.
"Commands" is a list expression in format of "<id>.<service>.<property> = <state>". The <id> is the device id. The <service> is the name of the service. The <property> is the name of the property. The <state> is a value that user want to set. The value of <state> can be bool, int, string, etc.

# Input
1. User request: describe what commands the user want to do on the target devices.
2. Device list: the information of devices related with user request {id, name, area, type and services}. Each service of the device may contains multiple properties.

# Workflow
1. Under the user request, find what actions the user want to do.
2. For each action, find the corresponding device, service and its property. And generate the action expression based on action and the property details.
3. Return the action expressions in a list.
4. In the process below, you need to consider the following situations:
Case 1: If there are multiple devices that match the user request and you cannot determine the target device, you should tell the user the devices and ask the user to provide more information.
Case 2: If you cannot find the corresponding device, service or property, you should tell the user that the device is not found or the device/service does not support the service/property and ask the user to provide more information.
Case 3: If you cannot fill in the value of the property in action because the user request is ambiguous or the value the user provided is out of the value range or illegal, you should tell the user what's wrong and ask the user to provide more information.

# Output
Your output should AlWAYS in the following format:
${format_example}
'''

INIT_USER_MESSAGE = '''
---User request---
${user_request}
---Device list---
${device_list}
'''

FORMAT_EXAMPLE = '''
---
According to your workflow, your have two Action_type: AskUser and Finish.
In AskUser type, you must return a json including "Action_type" and "Say_to_user". "Say_to_user" is the response to the user in oral language. 
In Finish type,you must return a json including "Action_type""Thought" ,"Commands" and "Say_to_user". "Thought" is the reasoning process of how you generate the commands.
Please note that the language of "Say_to_user" should be in the same language as the user request.

# Examples
Given the device list is as follows:
[{'id': 1, 'area': 'laboratory', 'type': 'light', 'services': {'light': {'on': {'description': 'Switch Status', 'format': 'bool', 'access': ['read', 'write', 'notify']}, 'brightness': {'description': 'Brightness', 'format': 'uint16', 'access': ['read', 'write', 'notify'], 'unit': 'percentage', 'value-range': [1, 65535, 1]}}}}]
Then given the following user request:
Case 1: "turn on the light", your output should be:
{
    "Thought": "There is only one command in the user request: 1. turn on the light. For command 1, there is only one light and user does not specify the area, so target device is the light in the laboratory. The device id is 1. The service is light. The property is on.",
    "Commands": [
        "1.light.on = true"
    ],
    "Say_to_user": "Ok, I have turned on the light in the laboratory for you.",
    "Action_type": "Finish"
}
Case 2: "打开电视机", your output should be:
{
    "Thought": "There is only one command in the user request: 1. turn on the TV. For command 1, there is no TV in the device list.",
    "Say_to_user": "抱歉，我找不到电视机。请您提供更多信息。",
    "Action_type": "AskUser"
}
Case 3: "turn on the light in the laboratory and set the brightness", your output should be:
{
    "Thought": "There are two commands in the user request: 1. turn on the light in the laboratory and 2. set the brightness. For command 1, there is only one light in the laboratory. The device id is 1. The service is light. The property is on. The state is true. For command 2, the target device is as same as command 1. The property is brightness, but the target state is not specified, so I need to ask the user for more information.",
    the brightness is not specified.",
    "Say_to_user": "Sorry, please tell me the brightness you want to set.",
    "Action_type": "AskUser"
}
Case 4: After Case 3, user response "set the brightness to 50%", your output should be:
{
    "Thought": "The user has provided the brightness value: 50%. Since the format of brightness is uint16, the value range is [1, 65535, 1]. So the target state is 32768 for command 2.",
    "Commands": [
        "1.light.on = true",
        "1.light.brightness = 32768"
    ],
    "Say_to_user": "Ok, I have turned on the light in the laboratory and set the brightness to 50% for you.",
    "Action_type": "Finish"
}
---
'''

OUTPUT_MAPPING = {}

class ControlDevice(Action):
    def __init__(self, name="DeviceControler", context=None):
        super().__init__(name, context)
        self.llm = LLM()

    def parse_output(self, output: str) -> dict:
        # TODO error handling
        if output.startswith("```json"):
            output = output[7:]
            output = output[:-3]
            return json.loads(output.strip())
        elif output.startswith("```"):
            output = output[3:]
            output = output[:-3]
            return json.loads(output.strip())
        else:
            return json.loads(output.strip())

    async def run(self, history_msg: list[Message], user_input: Message) -> Message:
        _logger.info(f"DeviceControler run: {user_input}")
        # 根据来源判断是第一次用户输入还是用户回复
        if user_input.sent_from == "Manager":
            user_request = user_input.content
            self.llm.reset()
            SYSTEM_MESSAGE_Template = Template(SYSTEM_MESSAGE)
            self.llm.add_system_msg(SYSTEM_MESSAGE_Template.substitute(format_example=FORMAT_EXAMPLE))
            
            all_context = CONFIG.hass_data["all_context"]
            INIT_USER_MESSAGE_Template = Template(INIT_USER_MESSAGE)
            self.llm.add_user_msg(INIT_USER_MESSAGE_Template.substitute(user_request=user_request, device_list=all_context))
        else:
            user_response = user_input.content
            self.llm.add_user_msg(user_response)
        
        try:
            loop = asyncio.get_running_loop()
            rsp = await loop.run_in_executor(None, self.llm.chat_completion_json_v1, self.llm.history)

            _logger.info(f"DeviceControler rsp: {rsp}")
            rsp_json = self.parse_output(rsp)

            if rsp_json["Action_type"] == "Finish":
                commands = rsp_json["Commands"]
                say_to_user = rsp_json["Say_to_user"]
                # say_to_user = rsp_json["Say_to_user"] + "/n" + "/n".join(commands)
                self.llm.reset()
                TRANSLATOR = Translator()
                for command in commands:
                #     # await TRANSLATOR.run_single_command(command)
                #     # 不等设备执行完成
                    loop.create_task(TRANSLATOR.run_single_command(command))
                return Message(role=self.name, content=say_to_user, send_to=["User"], sent_from="DeviceControler", cause_by="Finish")
            elif rsp_json["Action_type"] == "AskUser":
                self.llm.add_assistant_msg(rsp)
                say_to_user = rsp_json["Say_to_user"]
                return Message(role=self.name, content=say_to_user, send_to=["User"], sent_from="DeviceControler", cause_by="AskUser")
            else:
                self.llm.reset()
                return Message(role=self.name, content="Error: device_controler's action_type is wrong.", send_to=["User"], sent_from="DeviceControler", cause_by="Finish")
        except Exception as e:
            self.llm.reset()
            return Message(role=self.name, content="Some thing wrong in device_controler's process.", send_to=["User"], sent_from="DeviceControler", cause_by="Finish")
