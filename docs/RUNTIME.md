# 运行库隔离经验

精确后端曾在加载预编译缓存时失败，尚未执行模型：

1. 宿主的 `ONEAPI_DEVICE_SELECTOR=level_zero:0` 使 Triton 的扩展能力探测改变。
2. 仅移除选择器仍不足。当前固定 Triton 版本会优先通过 PATH 查找系统 icpx，再使用其SYCL环境；ComfyUI启动脚本加载的系统oneAPI与预编译时使用的Python运行库不同。

本机修复只作用于NR子进程：排除系统oneAPI/icpx搜索路径，清除相关覆盖，先加载所选Python `Library/bin/sycl9.dll`，再加载其他运行库。精确target、驱动、源码与缓存哈希校验保留；不能通过修改预期target绕过失败。

`reference/runtime_environment.py` 保存本机采用的隔离实现，供后端集成。节点本身不向宿主应用这些环境修改。这个文件不是完整运行库安装器，也不替代显卡/驱动兼容性检测。
