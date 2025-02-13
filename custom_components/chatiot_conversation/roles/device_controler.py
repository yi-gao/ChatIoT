from roles.role import Role
from actions.control_device import ControlDevice

class DeviceControler(Role):
    def __init__(self, name="", profile="DeviceControler", goal="Control devices in the home based on user requests", **kwargs):
        super().__init__(name=name, profile=profile, goal=goal, **kwargs)
        self._init_actions([ControlDevice])
        self._watch(["UserInput"])
        