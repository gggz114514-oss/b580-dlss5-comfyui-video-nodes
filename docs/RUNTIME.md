# 运行库隔离经验

精确后端曾在加载预编译缓存时失败，尚未执行模型：

1. 宿主的 `ONEAPI_DEVICE_SELECTOR=level_zero:0` 使 Triton 的扩展能力探测改变。
2. 仅移除选择器仍不足。当前固定 Triton 版本会优先通过 PATH 查找系统 icpx，再使用其SYCL环境；ComfyUI启动脚本加载的系统oneAPI与预编译时使用的Python运行库不同。

本机修复只作用于NR子进程：排除系统oneAPI/icpx搜索路径，清除相关覆盖，先加载所选Python `Library/bin/sycl9.dll`，再加载其他运行库。精确target、驱动、源码与缓存哈希校验保留；不能通过修改预期target绕过失败。

`reference/runtime_environment.py` 保存本机采用的隔离实现，供后端集成。节点本身不向宿主应用这些环境修改。这个文件不是完整运行库安装器，也不替代显卡/驱动兼容性检测。

便携安装追加处理：Windows PowerShell 子进程只使用自身的模块路径，避免继承 PowerShell 7 的模块；ZIP校验与解压使用 .NET。Triton 的原生 getenv 在中文路径上会发生 ANSI/UTF-8 解码冲突，便携 bootstrap 因此通过 `knobs.cache.dir` 的 Python 接口设置 Unicode 缓存路径。该修复不更改模型、算子或缓存哈希规则。
