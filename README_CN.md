<div align="center">

<h1 align="center">🏠ChatIoT</h1>
一个能够轻松控制智能家居的语音助手。

[English](./README.md) / 简体中文
</div>

## 📝 简介
ChatIoT主要的目的是让用户无需编写代码或者点击操作来与物联网设备进行交互。

本项目聚焦智能家居领域，使用Home Assistant作为基础平台。用户在Home Assistant上安装Home Assistant后可以通过自然语言实现如下功能：
- 控制设备，如“打开书房的灯”
- 创建规则，如“如果有人经过客厅，自动打开客厅的灯”

<p align="center">
<a href=""><img src="docs\resources\ChatIoT_overview.png" width="500px"></a>
</p>

## 安装准备
在使用ChatIoT之前，你需要做一些准备工作。
### 1. 安装Home Assistant
首先，需要在本地安装Home Assistant，这里推荐采用docker方式进行安装。

接着，需要在Home Assistant中安装HACS集成。

最后，可以在HACS商店中安装特定的集成将你的设备接入到Home Assistant中。

详细教程参考[Home Assistant安装指南](./docs/Home_Assistant_Setup_CN.md)。

**注意**：目前支持Xiaomi Home和Xiaomi MIoT Auto集成接入的米家设备。如果你没有这类设备但依然想体验ChatIoT，你可以使用设备模拟器来模拟设备，创建你的虚拟家庭环境。详细教程参考[Miot设备模拟指南](./docs/Miot_Device_Setup_CN.md)。

### 2. 大模型API Key获取
ChatIoT基于大型语言模型实现设备控制和创建规则。考虑到难以在本地部署部署大模型服务，目前ChatIoT采用API调用的方式。

以下是当前支持的API列表（需要支持OpenAI调用）：

- [qwen-max](https://bailian.console.aliyun.com/?spm=a2c4g.11186623.0.0.57c055effQCwnp#/model-market)[推荐]
- [qwen-plus](https://bailian.console.aliyun.com/?spm=a2c4g.11186623.0.0.57c055effQCwnp#/model-market)
- [qwen-turbo](https://bailian.console.aliyun.com/?spm=a2c4g.11186623.0.0.57c055effQCwnp#/model-market)
- [moonshot-v1-8k](https://platform.moonshot.cn/console/api-keys)
- [deepseek-chat](https://platform.deepseek.com/api_keys)
- [deepseek-reasoner](https://platform.deepseek.com/api_keys)

我们将很快支持更广泛的大语言模型调用。

## 🛠️ 安装

Home Assistant的自定义集成文件放在/config/custom_components目录下，因此安装的本质就是把ChatIoT文件放在这个目录下，有如下两种方式：

### Method 1: Git clone from Github
```bash
cd config # Home Assistant的配置文件
git clone https://github.com/zju-emnets/ChatIoT
cd chatiot
./install.sh /config # /config是Home Assistant容器中默认的位置，在外部挂载的配置文件夹中操作时填写外部的绝对路径
```

### Method 2: HACS

手动安装：

HACS > Overflow Menu > Custom repositories > Repository: https://github.com/zju-emnets/ChatIoT.git & Category or Type: Integration > ADD > ChatIoT in New or Available for download section of HACS > DOWNLOAD

或点击下方按钮在HACS中进行安装：

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=Integration&repository=ChatIoT&owner=zju-emnets)

详细教程参见 [ChatIoT集成安装指南](./docs/ChatIoT_Integration_Setup_CN.md)。

## ✒️ Citation

如果ChatIoT对你的研究发表有帮助，欢迎在文中引用[ChatIoT](https://maestro.acm.org/trk/clickp?ref=z16l2snue3_2-310b8_0x33ae25x01410&doi=3678585)，使用如下BibTeX条目：

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
