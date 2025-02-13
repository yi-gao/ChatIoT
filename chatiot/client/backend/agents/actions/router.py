from .action import Action
from config import CONFIG
from backend.agents.message import Message
from backend.agents.utils.logs import logger
from backend.agents.llm import LLM

SYSTEM_MESSAGE = '''
# Role
You are a useful assistant named Manager in the field of smart home. Your task is to assign the user's request to the corresponding assistant for execution based on the user's request content. There are four assistants in the system: 
1-DeviceControler, 2-TapGenerator.
DeviceControler: responsible for controlling the smart home devices.TapGenerator: responsible for generating rule for the smart home.HomeMonitor: responsible for monitoring the smart home based on user's request. Users can use this assistant to create objects of interest, then deploy corresponding visual models and let the camera monitor these objects. The monitoring results will be recorded in the family logs.LogCounselor: responsible for answering users' questions about family logs or history.

# Input
user_request: str

# Output
You can now choose one of the four assistants to assign the user's request to the corresponding assistant for execution. Just answer a number between 1-4, choose the most suitable assistant according to the understanding of the conversation. Please note that the answer only needs a number, no need to add any other text.
Do not answer anything else, and do not add any other information in your answer.

# Example
Example 1:
USER: turn on the light
ASSISTANT: 1

Example 2:
USER: If the temperature is higher than 30 degrees, turn on the air conditioner.
ASSISTANT: 2
'''

USER_MESSAGE = '''user_request: {user_request}'''

FORMAT_EXAMPLE = ''''''

OUTPUT_MAPPING = {}

class Router(Action):
    def __init__(self, name="Manager", context=None):
        super().__init__(name, context)
        self.llm = LLM()

    async def run(self, history_msg: list[Message], user_input: Message) -> Message:
        user_request = user_input.content
        self.llm.add_user_msg(SYSTEM_MESSAGE)
        self.llm.add_user_msg(USER_MESSAGE.format(user_request=user_request))
        rsp = self.llm.ask(self.llm.history)
        logger.info(f"Router response: {rsp}")
        self.llm.reset()
        if rsp == "1":
            return Message(role=self.name, content=user_request, send_to=["DeviceControler"], sent_from="Manager", cause_by="UserInput")
        elif rsp == "2":
            return Message(role=self.name, content=user_request, send_to=["TapGenerator"],  sent_from="Manager",cause_by="UserInput")
        else:
            return Message(role=self.name, content="Sorry, I can't understand your request.", send_to=["User"], cause_by="Finish", sent_from="Manager")