"""Defines the ChatIoT Conversation backend."""
from __future__ import annotations

from .utils.logs import _logger
_logger.debug(f"Start conversation.py")

from typing import Literal
from homeassistant.components.conversation import ConversationInput, ConversationResult, AbstractConversationAgent, ConversationEntity
from homeassistant.components import assist_pipeline, conversation as ha_conversation
from homeassistant.components.conversation.const import DOMAIN as CONVERSATION_DOMAIN
from homeassistant.components.homeassistant.exposed_entities import async_should_expose
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv, intent, entity_registry as er, area_registry as ar, device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

from .const import (
    DOMAIN,
    CONF_PROVIDER,
    PROVIDERS,
    DEFAULT_PROVIDER,
    WORK_PATH
)

import sys
sys.path.append(WORK_PATH)

import requests
from configs import CONFIG
from context_assistant import download_instance, get_miot_info, get_miot_devices, get_all_states, get_all_context
from utils.utils import delete_all_files_in_folder

_logger.debug(f"conversation.py: module import completed")
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> bool:
    """Set up ChatIoT Conversation from a config entry."""

    def create_agent(provider):
        agent_cls = None
        if provider in PROVIDERS:
            agent_cls = GenericOpenAIAPIAgent
        else:
            _logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
        return agent_cls(hass, entry)

    provider = entry.data.get(CONF_PROVIDER, DEFAULT_PROVIDER)
    agent = await hass.async_add_executor_job(create_agent, provider)
    await agent._async_load_model(entry)
    async_add_entities([agent])
    return True

class LocalLLMAgent(ConversationEntity, AbstractConversationAgent):
    """Base Local LLM conversation agent."""
    hass: HomeAssistant
    entry_id: str
    history: dict[str, list[dict]]

    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id
        self._attr_supported_features = (
            ha_conversation.ConversationEntityFeature.CONTROL
        )
        self.hass = hass
        self.entry_id = entry.entry_id
        self.history = {}
        _logger.debug("start conversation")

    async def async_added_to_hass(self) -> None:
        """When entity is added to Home Assistant."""
        await super().async_added_to_hass()
        assist_pipeline.async_migrate_engine(
            self.hass, "conversation", self.entry.entry_id, self.entity_id
        )
        ha_conversation.async_set_agent(self.hass, self.entry, self)
    
    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from Home Assistant."""
        ha_conversation.async_unset_agent(self.hass, self.entry)
        await super().async_will_remove_from_hass()

    @property
    def entry(self) -> ConfigEntry:
        try:
            return self.hass.data[DOMAIN][self.entry_id]
        except KeyError as ex:
            raise Exception("Attempted to use self.entry during startup.") from ex
        
    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    def _load_model(self, entry: ConfigEntry) -> None:
        """Load the model on the backend. Implemented by sub-classes"""
        raise NotImplementedError()

    async def _async_load_model(self, entry: ConfigEntry) -> str:
        """Default implementation is to call _load_model() which probably does blocking stuff"""
        return await self.hass.async_add_executor_job(
            self._load_model, entry
        )
    
    def _generate(self, conversation: dict) -> str:
        """Call the backend to generate a response from the conversation. Implemented by sub-classes"""
        raise NotImplementedError()

    async def _async_generate(self, conversation: dict) -> str:
        """Default implementation is to call _generate() which probably does blocking stuff"""
        return await self.hass.async_add_executor_job(
            self._generate, conversation
        )

    def _warn_context_size(self):
        raise NotImplementedError()

    async def async_process(
        self, user_input: ConversationInput
    ) -> ConversationResult:
        _logger.debug(f"Processing conversation: {user_input.text}")
        """Process a sentence."""

        if user_input.conversation_id:
            conversation_id = user_input.conversation_id
        else:
            conversation_id = ulid.ulid()
        
        conversation = []
        _logger.debug(f"user_input: {user_input}")

        conversation = []

        conversation.append({"role": "user", "message": user_input.text})
            
        # generate a response
        try:
            _logger.debug(f"conversation_id: {conversation_id}")
            _logger.debug(f"conversation: {conversation}")
            response = await self._async_generate(conversation_id, conversation)
            _logger.debug(f"response: {response}")

        except Exception as err:
            _logger.error("There was a problem talking to the backend")
            
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.FAILED_TO_HANDLE,
                f"Sorry, there was a problem talking to the backend: {repr(err)}",
            )
            return ConversationResult(
                response=intent_response, conversation_id=conversation_id
            )
        
        conversation.append({"role": "assistant", "message": response})

        if conversation_id not in self.history:
            self.history[conversation_id] = conversation
        else:
            self.history[conversation_id].extend(conversation)
        
        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response.strip())

        return ConversationResult(
            response=intent_response, conversation_id=conversation_id
        )      

    def _async_get_exposed_entities(self) -> tuple[dict[str, str], list[str]]:
        """Gather exposed entity states"""
        # TODO consider the privacy of the user
        # Now ChatIoT can access all entities
        pass
        
    async def _reload_all(self):
        await self.hass.services.async_call("homeassistant", "reload_all")
        # access_token = CONFIG.hass_data["access_token"]
        # headers = {
        #     "Authorization": f"Bearer {access_token}",
        #     "Content-Type": "application/json"
        # }
        # url = "http://127.0.0.1:8123/api/services/homeassistant/reload_all"
        # try:
        #     def test():
        #         nonlocal url, headers
        #         response = requests.post(url=url, headers=headers)
        #         _logger.debug(f"response: {response}")
        #         return "reload all"
        #     response = await self.hass.async_add_executor_job(test)
        #     return response
        # except Exception as ex:
        #     _logger.error(f"Connection error was: {repr(ex)}")
        #     return "failed_to_connect"

    
    async def _check_config(self):
        # import time, asyncio
        # log_file_path = "/config/home-assistant.log"
        # error_tag = str(time.strftime('%Y-%m-%d %H:%M:%S'))
        # await self.hass.services.async_call("homeassistant", "check_config")
        # await asyncio.sleep(1)
        # _logger.debug(f"error_tag: {error_tag}")
        # with open(log_file_path, 'r') as f:
        #     lines = f.readlines()
        #     for line in lines[-20:]:
        #         _logger.debug(f"line: {line}")
        #         if error_tag in line and "ERROR" in line:
        #             return False
        # return True
        access_token = CONFIG.hass_data["access_token"]
        url = f"http://127.0.0.1:8123/api/config/core/check_config"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        try:
            def test():
                nonlocal url, headers
                response = requests.post(url=url, headers=headers)
                _logger.debug(f"response: {response}")
                if response.status_code == 200:
                    return response.json()["result"]
                else:
                    return f"failed_to_connect: {response.status_code}"
            response = await self.hass.async_add_executor_job(test)
            return response
        except Exception as ex:
            _logger.error(f"Connection error was: {repr(ex)}")
            return "failed_to_connect"

    # async def _get_states(self):
    #     access_token = CONFIG.hass_data["access_token"]
    #     headers = {
    #         "Authorization": f"Bearer {access_token}",
    #         "Content-Type": "application/json"
    #     }
    #     url = "http://127.0.0.1:8123/api/states"
    #     try:
    #         def test():
    #             nonlocal url, headers
    #             response = requests.get(url=url, headers=headers)
    #             _logger.debug(f"response: {response}")
    #             return "success"
    #         response = await self.hass.async_add_executor_job(test)
    #         return response
    #     except Exception as ex:
    #         _logger.error(f"Connection error was: {repr(ex)}")
    #         return "failed_to_connect"

class GenericOpenAIAPIAgent(LocalLLMAgent):
    """Generic OpenAI API conversation agent."""

    async def _async_load_model(self, entry: ConfigEntry) -> None:
        CONFIG.configs_llm["provider"] = entry.data[CONF_PROVIDER]
        CONFIG.configs_llm["api_key"] = entry.data["api_key"]
        CONFIG.configs_llm["base_url"] = entry.data["base_url"]
        CONFIG.configs_llm["temperature"] = entry.data["temperature"]
        CONFIG.configs_llm["max_tokens"] = entry.data["max_tokens"]
        CONFIG.hass_data["access_token"] = entry.data["access_token"]
        _logger.debug(f"configs_llm: {CONFIG.configs_llm}")
        _logger.debug(f"hass_data: {CONFIG.hass_data}")

        import os
        if os.path.exists("/config/.storage/chatiot_conversation/temp"):
            await self.hass.async_add_executor_job(delete_all_files_in_folder, "/config/.storage/chatiot_conversation/temp")
        # await self.hass.async_add_executor_job(delete_all_files_in_folder, "/config/.storage/chatiot_conversation/temp")
        await self.hass.async_add_executor_job(get_miot_devices)
        await self.hass.async_add_executor_job(download_instance)
        await self.hass.async_add_executor_job(get_miot_info)
        await get_all_states()
        await self.hass.async_add_executor_job(get_all_context)

        from jarvis import JARVIS
        self.jarvis = JARVIS
        from translator import Translator
        self.translator = Translator(self.hass)
    
    async def _async_generate(self, conversation_id: str, conversation: list[dict]) -> str:
        try:
            result = await self.jarvis.run(conversation[-1]["message"])
            _logger.debug(f"result: {result}")
            return result
        except Exception as err:
            _logger.error(f"Error generating response: {err}")
            return f"{err}"
        

    

