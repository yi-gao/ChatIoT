# get devices and entities
# compress the data
import os
import requests
from const import DATA_PATH
from configs import CONFIG
from utils.utils import get_json, write_json
from utils.logs import _logger
import asyncio


def download_instance():
    if not os.path.exists(f'{DATA_PATH}/temp/miot'):
        os.makedirs(f'{DATA_PATH}/temp/miot')
    if os.path.exists(f'{DATA_PATH}/temp/miot/model_type.json'):
        model_type = get_json(f'{DATA_PATH}/temp/miot/model_type.json')
        CONFIG.hass_data['model_type'] = model_type
    else:  
        url = 'http://miot-spec.org/miot-spec-v2/instances?status=all'
        res = requests.get(url)
        instances = res.json()
        model_type = {}
        for instance in instances["instances"]:
            model = instance['model']
            if model not in model_type:
                model_type[model] = instance['type']
        write_json(f'{DATA_PATH}/temp/miot/instances.json', instances)
        write_json(f'{DATA_PATH}/temp/miot/model_type.json', model_type)
        CONFIG.hass_data['model_type'] = model_type

def download_spec_by_model(model: str):
    if model not in CONFIG.hass_data['model_type']:
        _logger.error(f"Model {model} not found.")
        return None
    if not os.path.exists(f'{DATA_PATH}/temp/miot/spec'):
        os.makedirs(f'{DATA_PATH}/temp/miot/spec')
    if os.path.exists(f'{DATA_PATH}/temp/miot/spec/{model}.json'):
        return get_json(f'{DATA_PATH}/temp/miot/spec/{model}.json')
    else:
        miot_type = CONFIG.hass_data['model_type'][model]
        url = f'http://miot-spec.org/miot-spec-v2/instance?type={miot_type}'
        res = requests.get(url)
        spec = res.json()
        write_json(f'{DATA_PATH}/temp/miot/spec/{model}.json', spec)
        return spec

def download_spec_by_models(models: list[str]):
    for model in models:
        download_spec_by_model(model)


def convert_spec_to_info(spec: dict) -> dict:
    device_type = spec["type"].split(":")[3]
    device_type = device_type.replace("-", "_")
    info = {
        "type": device_type,
        "services": {}
    }
    for service in spec["services"][1:]:
        service_type = service["type"].split(":")[3]
        service_type = service_type.replace("-", "_")
        service_obj = {}
        for property in service.get("properties", []):
            property_type = property["type"].split(":")[3]
            property_type = property_type.replace("-", "_")
            property_value = {k: v for k, v in property.items() if k not in ["iid", "type"]}
            if property_value.get("access", []) != []:
                service_obj[property_type] = property_value   
        info["services"][service_type] = service_obj
        if info["services"][service_type] == {}:
            info["services"].pop(service_type)
    return info

def get_miot_info():
    miot_devices = CONFIG.hass_data['miot_devices']
    if not os.path.exists(f'{DATA_PATH}/temp/miot/info'):
        os.makedirs(f'{DATA_PATH}/temp/miot/info')
    for device in miot_devices:
        model = device["model"]
        if model == 'unknown':
            continue
        if os.path.exists(f'{DATA_PATH}/temp/miot/info/{model}.json'):
            continue
        if not os.path.exists(f'{DATA_PATH}/temp/miot/spec/{model}.json'):
            spec = download_spec_by_model(model)
        else:
            spec = get_json(f'{DATA_PATH}/temp/miot/spec/{model}.json')
        if spec:
            info = convert_spec_to_info(spec)
            write_json(f'{DATA_PATH}/temp/miot/info/{model}.json', info)

def get_miot_devices():
    device_file = "/config/.storage/core.device_registry"
    miot_devices = []
    devices_json = get_json(device_file)
    device_id_counter = 1
    for device in devices_json["data"]["devices"]:
        identifiers = device.get('identifiers', [])
        for identifier in identifiers:
            if identifier[0] == 'xiaomi_miot':
                area_id = device['area_id']
                model = device['model']
                # 条件判断name_by_user是否为null，不为空则使用name_by_user，否则使用name
                name = device['name_by_user']
                if name is None:
                    name = device['name']
                if '-' in identifier[1]:
                    mac_address = identifier[1].split('-')[0]
                else:
                    mac_address = identifier[1]
                miot_device_info = {
                    'id': device_id_counter,
                    'name': name,
                    'area': area_id if area_id else 'unknown',
                    'model': model if model else 'unknown',
                    'mac_address': mac_address,
                    'integration': 'xiaomi_miot'
                }
                miot_devices.append(miot_device_info)
                device_id_counter += 1
            elif identifier[0] == 'xiaomi_home':
                area_id = device['area_id']
                model = device['model']
                # 条件判断name_by_user是否为null，不为空则使用name_by_user，否则使用name
                name = device['name_by_user']
                if name is None:
                    name = device['name']
                # identifier[1] 直接判断关联实体
                miot_device_info = {
                    'id': device_id_counter,
                    'name': name,
                    'area': area_id if area_id else 'unknown',
                    'model': model if model else 'unknown',
                    'identifier': identifier[1],
                    'integration': 'xiaomi_home'
                }
                miot_devices.append(miot_device_info)
                device_id_counter += 1
    CONFIG.hass_data["miot_devices"] = miot_devices
    if not os.path.exists(f'{DATA_PATH}/temp/miot'):
        os.makedirs(f'{DATA_PATH}/temp/miot')
    write_json(f'{DATA_PATH}/temp/miot/devices.json', miot_devices)

async def get_all_states():
    loop = asyncio.get_event_loop()
    access_token = CONFIG.hass_data["access_token"]
    _logger.debug(f"access_token: {access_token}")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    url = "http://127.0.0.1:8123/api/states"
    def test():
        nonlocal url, headers
        return requests.get(url=url, headers=headers)

    response = await loop.run_in_executor(None, test)
    if response.status_code == 200:
        states = response.json()
        _logger.debug(f"states: \n{states}")
    else:
        _logger.error(f"Fail to get states: {response.status_code}: {response.text}")
    CONFIG.hass_data["states"] = states
    write_json(f'{DATA_PATH}/temp/miot/states.json', states)

def find_entity_by_entity_id(entity_id):
    entities = CONFIG.hass_data["states"]
    for entity in entities["data"]["entities"]:
        if entity["entity_id"] == entity_id:
            return entity
    return None    

def find_entity_by_field_mac(field, mac_address):
    additional_fields_original = ["illumination_sensor.illumination", "temperature_humidity_sensor.temperature", "temperature_humidity_sensor.relative_humidity"]
    additional_fields_new = ["illumination-2-1", "temperature-2-1", "relative_humidity-2-2"]
    for i, additional_field in enumerate(additional_fields_original):
        if field == additional_field:
            field = additional_fields_new[i]
            break
    entities = CONFIG.hass_data["states"]
    for entity in entities:
        attributes = entity.get("attributes", {})
        if field in attributes:
            if "mac_address" in attributes:
                if attributes.get("mac_address", "").lower() == mac_address.lower():
                    return entity
            elif "parent_entity_id" in attributes:
                parent_entity_state = find_entity_by_entity_id(attributes["parent_entity_id"])
                parent_attributes = parent_entity_state.get("attributes", {})
                if "mac_address" in parent_attributes:
                    if attributes.get("mac_address", "").lower() == mac_address.lower():
                        return entity
    return None    

def find_entities_by_device(device):
    entities_by_device = []
    mac_address = device['mac_address']
    for entity in CONFIG.hass_data["states"]:
        attributes = entity.get("attributes", {})
        if "mac_address" in attributes:
            if attributes.get("mac_address", "").lower() == mac_address.lower():
                entities_by_device.append(entity)
        elif "parent_entity_id" in attributes:
            parent_entity = find_entity_by_entity_id(attributes["parent_entity_id"])
            parent_attributes = parent_entity.get("attributes", {})
            if "mac_address" in parent_attributes:
                if attributes.get("mac_address", "").lower() == mac_address.lower():
                    entities_by_device.append(entity)
    return entities_by_device

def find_entities_by_indentifier(identifier):
    entities_by_identifier = []
    for entity in CONFIG.hass_data["states"]:
        if identifier in entity["entity_id"]:
            entities_by_identifier.append(entity)
    return entities_by_identifier

def get_all_context():
    miot_devices = CONFIG.hass_data['miot_devices']
    get_miot_info()
    all_context = []
    for device in miot_devices:
        single_device_context = {}
        model = device['model']
        info = get_json(f'{DATA_PATH}/temp/miot/info/{model}.json')
        _logger.debug(f"info: {info}")
        single_device_context['id'] = device['id']
        single_device_context['name'] = device['name']
        single_device_context['area'] = device['area']
        single_device_context['type'] = info['type']
        services = info['services']
        # service_to_remove = []
        # for service_name, service in services.items():
        #     property_to_remove = []
        #     for property_name, _ in service.items():
        #         field = f"{service_name}.{property_name}"
        #         _logger.debug(f"field: {field}")
        #         entity = find_entity_by_field_mac(field, device['mac_address'])
        #         if entity is None:
        #             property_to_remove.append(property_name)
        #     for property_name in property_to_remove:
        #         service.pop(property_name)
        #     if service == {}:
        #         service_to_remove.append(service_name)
        # for service_name in service_to_remove:
        #     services.pop(service_name)
        single_device_context['services'] = services
        all_context.append(single_device_context)
    CONFIG.hass_data['all_context'] = all_context
    write_json(f'{DATA_PATH}/temp/miot/all_context.json', all_context)

# TODO
def get_related_context(request: str):
    pass

if __name__ == "__main__":
    print(get_all_states())
