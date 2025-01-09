<div align="center">

<h1 align="center">🏠ChatIoT</h1>
A voice assistant that enables you to effortlessly create a smart home.

English / [简体中文](./README_CN.md)
</div>


## :pencil: Introduction
The mission of ChatIoT is to empower users to create TAP (Trigger-action Program) through natural language interactions. 

This repository is dedicated to the smart home domain, utilizing the Home Assistant open-source platform as its core infrastructure. Once ChatIoT is deployed, users can effortlessly control smart home devices using natural language (e.g., 'Turn on the lights in study room') or create TAP rules to automate tasks (e.g., 'If someone passes through the living room, automatically turn on the living room lights').

<p align="center">
<a href=""><img src="docs\resources\ChatIoT_overview.png" width="500px"></a>
</p>

## Pre-requests
Before using ChatIoT, you need to do some preparation.
### 1. Home Assistant Setup
See more details in [Home Assistant Setup Guide](./docs/Home_Assistant_Setup.md).

First, you need to install a Home Assistant locally and connect to your home devices.

Then, you need to install the HACS integration in Home Assistant (this requires your own GitHub account).

Finally, you can install the Xiaomi Miot Auto integration in the HACS store and then integrate your devices from Mi Home into Home Assistant.

**Note:** Currently, ChatIoT only supports Xiaomi devices integrated through Xiaomi Miot Auto. If you don't have this type of device, or you just want to experience ChatIoT, you can use the device simulator to simulate the device to generate your virtual home. See more details in [Miot Device Setup Guide](./docs/Miot_Device_Setup.md) .

### 2. LLM API Setup
ChatIoT is powered by Large Language Models (LLMs). Given the challenges associated with local deployment of LLMs, it currently utilizes API calls. Therefore, you will need to acquire an LLM API key.

Below is the current list of recommended APIs:
- gpt-3.5-turbo
- gpt-4-turbo
- gpt-4o
- deepseek-chat
- moonshot-v1-8k

Support for a broader range of APIs will be available soon.


## :hammer_and_wrench: Get Started
**There are two methods to deploy ChatIoT.**

If you just want to use ChatIoT, it is recommended to deploy it through Home Assistant integration.

### :whale: Deploy via HASS Integration (Recommended)
ChatIoT can be installed and deployed directly in Home Assistant through HACS integration.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=Integration&repository=ChatIoT&owner=ifcarpediem)

Please see the [Integration Setup Guide](./docs/ChatIoT_Integration_Setup.md) for more information.

### :computer: Deploy Locally
If you want to modify ChatIoT but are not familiar with Home Assistant and do not want your modifications to be affected by Home Assistant, you can choose to deploy ChatIoT locally and only use Home Assistant as a device interface.

Please see the [Deploy Locally Setup Guide](./docs/Deploy_Locally_Setup.md) for more information on installion on your local device.

## :black_nib: Citation
To cite [ChatIoT](https://maestro.acm.org/trk/clickp?ref=z16l2snue3_2-310b8_0x33ae25x01410&doi=3678585) in publications, please use the following BibTeX entries.

```bibtex
@article{gao2024chatiot,
  title={ChatIoT: Zero-code Generation of Trigger-action Based IoT Programs},
  author={Gao, Yi and Xiao, Kaijie and Li, Fu and Xu, Weifeng and Huang, Jiaming and Dong, Wei},
  journal={Proceedings of the ACM on Interactive, Mobile, Wearable and Ubiquitous Technologies},
  volume={8},
  number={3},
  pages={1--29},
  year={2024},
  publisher={ACM New York, NY, USA}
}
```
