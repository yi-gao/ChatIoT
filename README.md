<div align="center">

<h1 align="center">🏠ChatIoT</h1>
A smart assistant that makes it easy to control smart homes.

[English](./README.md) / 简体中文
</div>

## 📝 Introduction
The main goal of ChatIoT is to enable users to interact with IoT devices without writing code or clicking through operations.

This project focuses on the smart home domain, using Home Assistant as the foundational platform. After installing Home Assistant, users can achieve the following functionalities through natural language:
- Control devices, such as "Turn on the study room light."
- Create rules, such as "If someone passes the living room, automatically turn on the living room light."

<p align="center">
<a href=""><img src="docs\resources\ChatIoT_overview.png" width="500px"></a>
</p>

## Installation Preparation
Before using ChatIoT, you need to complete some preparatory steps.
### 1. Install Home Assistant
First, you need to install Home Assistant locally. It is recommended to use Docker for installation.

Next, you need to install the HACS integration in Home Assistant.

Finally, you can install specific integrations from the HACS store to connect your devices to Home Assistant.

For detailed instructions, refer to the [Home Assistant Installation Guide](./docs/Home_Assistant_Setup_CN.md).

**Note**: Currently, ChatIoT supports Xiaomi Home and Xiaomi MIoT Auto integrations for connecting Mi Home devices. If you do not have such devices but still want to experience ChatIoT, you can use a device simulator to create a virtual home environment. For detailed instructions, refer to the [Miot Device Simulation Guide](./docs/Miot_Device_Setup_CN.md).

### 2. Obtain a Large Model API Key
ChatIoT leverages large language models for device control and rule creation. Given the difficulty of deploying large model services locally, ChatIoT currently uses API calls.

Below is a list of currently supported APIs (requires support for OpenAI calls):

- [qwen-max](https://bailian.console.aliyun.com/?spm=a2c4g.11186623.0.0.57c055effQCwnp#/model-market)[Recommended]
- [qwen-plus](https://bailian.console.aliyun.com/?spm=a2c4g.11186623.0.0.57c055effQCwnp#/model-market)
- [qwen-turbo](https://bailian.console.aliyun.com/?spm=a2c4g.11186623.0.0.57c055effQCwnp#/model-market)
- [moonshot-v1-8k](https://platform.moonshot.cn/console/api-keys)
- [deepseek-chat](https://platform.deepseek.com/api_keys)
- [deepseek-reasoner](https://platform.deepseek.com/api_keys)

We will soon support a broader range of large language model calls.

## 🛠️ Installation

Home Assistant custom integration files are placed in the `/config/custom_components` directory. Therefore, installation essentially involves placing the ChatIoT files in this directory. There are two methods:

### Method 1: Git Clone from Github
```bash
cd config # Home Assistant configuration directory
git clone https://github.com/zju-emnets/ChatIoT
cd chatiot
./install.sh /config # /config is the default location in the Home Assistant container. Use the external absolute path when operating in the externally mounted configuration folder.
```

### Method 2: HACS

HACS > Overflow Menu > Custom repositories > Repository: https://github.com/zju-emnets/ChatIoT.git & Category or Type: Integration > ADD > ChatIoT in New or Available for download section of HACS > DOWNLOAD

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=Integration&repository=ChatIoT&owner=zju-emnets)

For detailed instructions, refer to the [ChatIoT Integration Installation Guide](./docs/ChatIoT_Integration_Setup_CN.md).

## ✒️ Citation

If ChatIoT has been helpful for your research publication, please cite [ChatIoT](https://maestro.acm.org/trk/clickp?ref=z16l2snue3_2-310b8_0x33ae25x01410&doi=3678585) using the following BibTeX entry:

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