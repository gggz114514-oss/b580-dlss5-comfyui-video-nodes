# B580 DLSS5 / NR ComfyUI Video Nodes

Intel Arc B580 上的实验性 NR 视频节点：精确计算后端，以及画面有差异的快速“类 DLSS5”后端，可串联 XeSS SR 和 FG。

**v0.2.0-pre 提供完整后端运行包与安装器。** 将节点放进 ComfyUI 的 custom_nodes，运行 `Install.bat`，重启后即可连接 VIDEO 节点。安装器自动获取独立 Python、Torch/XPU、Triton、预编译内核、GPU worker 和固定版本模型资源，不需要手动配置开发路径或安装编译器。

[下载预发布版本](https://github.com/gggz114514-oss/b580-dlss5-comfyui-video-nodes/releases/tag/v0.2.0-pre)。运行包约 1.86 GB，建议预留至少 12 GB 安装及工作空间。目标为 Windows x64 / Intel Arc B580；硬件和驱动仍受已验证缓存约束。

本项目不是 NVIDIA 官方 DLSS 产品，也不属于 NVIDIA、Intel 或 ComfyUI 官方项目。仓库名称用于说明实验方向，不代表认证或授权。

## 两个节点

| 节点 | 行为 |
|---|---|
| NR 视频（B580） | 同分辨率 NR 视频处理 |
| NR + XeSS SR + FG（B580） | NR → XeSS SR/AA → FG；SR 倍率可调 |

均提供 **精确版** 和 **快速版（类 DLSS5）**。快速版与精确版有明显画面差异，不能当作等价替代。精确版指经过参考 GPU 对照验证的计算后端；最终视频还经过格式转换和有损编码，不是浮点参考输出的字节副本。本仓库不包含用于独立复核模型等价性的权重和完整数据集。

1× SR 实际运行 XeSS AA。FG 输出帧率为输入的两倍、帧数为 `2N−1`，不补造末尾重复帧。GPU Block 提供原始帧运动信息；增强画面不覆盖下一次运动估计所需的原始颜色历史。NR/SR/FG 中间不通过 CPU 像素管道或中间视频传递。

## 安装与使用

需要 Windows x64、Intel Arc B580，以及有 Load Video / Save Video / VIDEO API 的 ComfyUI。独立后端随包提供，不改 ComfyUI 的 Python 环境。

1. 下载本仓库 ZIP，解压到 `ComfyUI/custom_nodes/b580-dlss5-comfyui-video-nodes`，确保目录内能看到 `__init__.py` 和 `Install.bat`。
2. 如果有旧的 `NR-B580-Local`，先禁用旧节点，避免同名注册。
3. 双击 `Install.bat`。它自动下载29个小分片，校验后重组为三份运行包，以及固定版本的上游模型资源；安装到节点目录的 `.runtime`。需要网络访问 GitHub。
4. 重启 ComfyUI，搜索 **NR B580**。连接 **Load Video → NR 节点 → Save Video**，在 Load Video 上传输入文件。
5. 可导入 `examples/single-nr-workflow.json` 或 `examples/nr-sr-fg-workflow.json`，再选自己的视频。另有 `*-api.json` 供 API 调用。画布模板已检查连接结构，尚未在全部前端版本中验收。

没有安装时节点会明确提示运行安装器。可选的 `config.json` / `NR_COMFY_CONFIG` 供高级用户覆盖运行位置与输出目录，普通安装无需填写。任务文件默认保存在 `.runtime/jobs`，Save Video 可另存到 ComfyUI 输出目录。

手动下载 Release 的全部 `.zip.partXX` 分片到同一目录后，也可执行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -AssetDirectory "D:\下载的运行包"`；仍会校验附件，模型资源首次需要联网。升级时请使用新的节点目录，安装器不会覆盖已有 `.runtime`。搬动目录后见 [便携说明](docs/PORTABLE.md)。

## 当前限制

- 输入为 SDR、8-bit 4:2:0、恒定帧率 H.264/HEVC 文件。
- 快速后端准备的输入尺寸：256×256、864×480、1920×1080；精确后端另有512×512。未准备尺寸报错，不自动缩小输入。
- 本机完整节点验收素材为864×480。不能把本体缓存覆盖范围等同于所有尺寸的完整节点验收。
- SR 1×和2×已有内部链路测试；其他倍率保持宽高比取整，由 SDK 检查支持范围。
- 最终封装复制第一条音轨。MP4 不兼容的音频编码可能报错，不静默丢音轨。
- 单次处理上限30分钟，支持 ComfyUI 取消任务。多个 NR 任务由后端租约串行化。
- 当前不承诺 A 系列、其他 B 系列或任意驱动可用，也没有发布到 ComfyUI Manager。

## 阶段成果与后续

见 [阶段验证](docs/VALIDATION.md)、[后端接口](docs/BACKEND.md)、[便携说明](docs/PORTABLE.md) 和 [运行环境隔离](docs/RUNTIME.md)。本机已从 ZIP 在独立中文路径完成安装、模型获取、默认节点发现及完整视频验证；这不等于其他电脑或任意驱动已验证。
