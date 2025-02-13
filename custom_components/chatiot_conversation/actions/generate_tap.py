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
You are a useful assistant named TapGenerator in the field of smart home. Your task is to parse user input into trigger-action program（TAP）.TAP consists of three parts: trigger, condition and action. The trigger is the event that triggers the automation. The condition is the condition that must be met for the automation to run. The action is the task that the automation will perform. The trigger and action are required, while the condition is optional.

# Input
1. User request: describe the automation the user want to create.
2. Device list: the information of devices related with user request: id, area, type and services. Each service of the device may contains multiple properties.

# Workflow
1. Understand the user's request, and extract the trigger, condition and action in the user request.
2. Find the corresponding device, service and its properties based on the trigger, condition and action.
3. Generate the TAP in target format, and return the TAP.
4. In the process below, you need to consider the following situations:
Case 1: If you cannot find clear trigger or action, you should tell the user that they missed some information.
Case 2: If you canot find the corresponding device or service, you should tell the user that the device or service is not found.
Case 3: If there are multiple devices that match the user request, you should ask the user to provide more information.
Case 4: If you have found the corresponding device and service, but you cannot fill in the value of the property in TAP because the user request is ambiguous, you should ask the user to provide more information.

# Output
Your output should AlWAYS in the following format:
${format_example}
'''

INIT_USER_MESSAGE = '''
---User_request---
${user_request}
---Device_list---
${device_list}'''

FORMAT_EXAMPLE = '''
---
According to your workflow, your have two Action_type: AskUser and Finish.
In AskUser type, you must return a json including "Thought", "Action_type" and "Say_to_user". "Say_to_user" is the response to the user to ask for more information. 
In Finish type,you must return a json including "Thought" ,"Action_type", "TAP" and "Say_to_user". "Thought" is the reasoning process of how you generate the TAP. "TAP" is a json expression in format of {"trigger": <trigger>, "condition": <condition>, "action": <action>}. <trigger>, <condition> and <action> are formed by basic elements "id.service.property<op><state>". The <op> in <trigger> and <condition> is chosen from "<", ">", or "==" while the <op> in <action> must be "=" . The <state> is a value which can be of various types based on the property type, including bool, int, and string. In <trigger> and <action>, elements are separated by ",". In <condition>, elements are combined using "and", "or" and "()", such as "condition_1&& (condition_2||condition_3)".
Please note that the language of "Say_to_user" should be in the same language as the user request.

# Examples
Given the device list is as follows:
[{"id":1,"area":"living room","type":"light","services":{"light":{"on":{"description":"Switch Status","format":"bool","access":["read","write","notify"]},"brightness":{"description":"Brightness","format":"uint16","access":["read","write","notify"],"unit":"percentage","value-range":[1,65535,1]},"color_temperature":{"description":"Color Temperature","format":"uint32","access":["read","write","notify"],"unit":"kelvin","value-range":[2700,6500,1]}}}},{"id":2,"area":"entry door","type":"magnet_sensor","services":{"magnet_sensor":{"illumination":{"description":"Illumination","format":"uint8","access":["read","notify"],"value-list":[{"value":1,"description":"Weak"},{"value":2,"description":"Strong"}]},"contact_state":{"description":"Contact State","format":"bool","access":["read","notify"]}}}},{"id":3,"name":"光照度传感器","area":"living room","type":"illumination_sensor","services":{"illumination_sensor":{"illumination":{"description":"Illumination","format":"float","access":["read","notify"],"unit":"lux","value-range":[0,83000,1]}}}}]
Then given the following user request:
Case 1: "turn on the light when I come back home.", your output should be:
{
    "Thought": "Based on the user request, the trigger is 'come back home', the action is 'turn on the light' and there is no condition. For the trigger, the device is the magnet_sensor in the entry door and the id is 2. The service is magnet_sensor. The property is contact_state. The state is true. For the action, the device is the light in the living room and the id is 1. The service is light. The property is on. The state is true.",
    "TAP": {
        "trigger": "2.magnet_sensor.contact_state==true",
        "condition": "",
        "action": "1.light.on=true"
    },
    "Say_to_user": "Ok, I have generated the TAP for you.",
    "Action_type": "Finish"
}
Case 2: "当我回家的时候，打开电视", your output should be:
{
    "Thought": "Based on the user request, the trigger is '当我回家的时候', the action is '打开电视' and there is no condition. For the trigger, the device is the magnet_sensor in the living room and the id is 2. The service is magnet_sensor. The property is contact_state. The state is true. For the action, there is no TV in the device list.",
    "Say_to_user": "抱歉，我找不到电视机。请您提供更多信息。",
    "Action_type": "AskUser"
}
Case 3: "当客厅比较暗时，打开灯", your output should be:
{
    "Thought": "Based on the user request, the trigger is '家里比较暗', the action is '打开灯' and there is no condition. For the trigger, the device is the illumination_sensor in the living room and the id is 3. The service is illumination_sensor. The property is illumination. The op is <. '比较暗' is a fuzzy concept, I predefined the range of '比较暗' is [0, 50] lux. The state is 50, but I need to confirm it with the user. For the action, the device is the light in the living room and the id is 1. The service is light. The property is on. The state is true.",
    "Say_to_user": "一般来说，家里比较暗是指光照度小于50勒克斯。请问您是否同意这个阈值？",
    "Action_type": "AskUser"
}
Case 4: After Case 3, user response "是", your output should be:
{
    "Thought": "The user agreed that '比较暗' is less than 50 lux. So the state of the trigger is 50. The TAP is generated successfully.",
    "TAP": {
        "trigger": "3.illumination_sensor.illumination<50",
        "condition": "",
        "action": "1.light.on=true"
    },
    "Say_to_user": "Ok, I have generated the TAP for you.",
    "Action_type": "Finish"
}
---
'''

OUTPUT_MAPPING = {}

class GenerateTAP(Action):
    def __init__(self, name="TAPGenerator", context=None):
        super().__init__(name, context)
        self.llm = LLM()
        self.user_request = None

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
        _logger.info(f"TapGenerator run: {user_input}")
        if self.user_request is None:
            self.user_request = user_input.content
        if user_input.sent_from == "Manager":
            self.llm.reset()
            user_request = user_input.content
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

            _logger.info(f"TapGenerator rsp: {rsp}")
            # TODO error handling
            rsp_json = self.parse_output(rsp)
            if rsp_json["Action_type"] == "Finish":
                tap = rsp_json["TAP"]
                say_to_user = rsp_json["Say_to_user"]
                # say_to_user = rsp_json["Say_to_user"] + "\n" + str(tap)
                TRANSLATOR = Translator()
                # await TRANSLATOR.deploy_tap(self.user_request, tap)
                loop.create_task(TRANSLATOR.deploy_tap(self.user_request, tap))
                self.user_request = None
                self.llm.reset()
                return Message(role=self.name, content=say_to_user, send_to=["User"], cause_by="Finish", sent_from="TAPGenerator")
            elif rsp_json["Action_type"] == "AskUser":
                self.llm.add_assistant_msg(rsp)
                say_to_user = rsp_json["Say_to_user"]
                return Message(role=self.name, content=say_to_user, send_to=["User"], cause_by="AskUser", sent_from="TAPGenerator")
            else:
                self.user_request = None
                self.llm.reset()
                return Message(role=self.name, content="Error: tap_generator's action_type is wrong,", send_to=["User"], cause_by="Finish", sent_from="TAPGenerator")
        except Exception as e:
            self.user_request = None
            self.llm.reset()
            return Message(role=self.name, content="Some thing wrong in tap_generator's process.", send_to=["User"], cause_by="Finish", sent_from="TAPGenerator")
