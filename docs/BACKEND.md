# 外部后端接口

节点仅负责 ComfyUI VIDEO 输入输出和进程生命周期。推理不在 ComfyUI 主进程内执行，ComfyUI 自动模型补丁不会自动作用于 NR。

配置的 `gpu_lease` 接收 `--owner ID --cwd DIR --log FILE --timeout-seconds 1800 --wait-seconds 0 -- PYTHON RUNNER --request FILE`，负责互斥与超时终止进程树。此脚本与 runner 均须由兼容后端提供，本仓库不提供替代的推理实现。

请求 JSON：

```json
{"input":"D:/videos/input.mp4","mode":"exact","combo":false,"scale":1.0}
```

`mode` 为 exact/fast；combo=true 启用 SR+FG。请求文件的父目录就是作业目录。runner 成功须退出0，写入 `result.json`：

```json
{"passed":true,"output":"D:/NR-output/jobs/id/nr-video.mp4"}
```

失败须非零退出并尽可能记录 `{"passed":false,"error":"说明"}`。节点保留日志并报错。取消时创建作业内的 `cancel.flag`，等待10秒，超时仅终止该任务进程树。

后端须自行验证尺寸、帧率、输出帧数、模型/缓存兼容性；保护GPU资源所有权与同步；不允许失败后静默跳过 NR。原始帧 GPU Block 运动及原始颜色历史不应被增强结果替代。
