# 组件归属

运行包保留 Python、PyTorch、Triton、NumPy、PyAV、OpenVINO 等依赖的许可证和 wheel 元数据；原生运行包的 XeSS、oneVPL、FFmpeg 许可及来源见 `.runtime/licenses`。补充的 MSVC 再分发清单和 Depth Anything V2 Small 许可证见本仓库 `licenses`。

Depth Anything V2 Small 的来源为 https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf ，随包为其 OpenVINO IR 转换。FFmpeg 为未修改的 Gyan 7.1 essentials 构建，GPLv3及对应源码/构建来源记于 `.runtime/licenses/THIRD_PARTY_NOTICES.md`。

NR 使用固定社区参考资源，由安装器从上游下载、校验后在本机提取；它不是本仓库授予开源许可的权重。本仓库未附原始 NR 权重或 NVIDIA DLL。

GPU Block 的项目私有实现仅提供编译后的运行组件，不提供其源码或含源码的调试产物。各第三方组件仍受各自原许可约束。
