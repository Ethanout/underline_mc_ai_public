# QQ 连接自动恢复

`start_ui.bat` 启动一个隐藏的恢复进程。即使资料服务已启动，也会补起恢复进程。系统文件锁确保只有一个恢复进程。进程不调用模型，不消耗 token。

每 30 秒读取 NapCat 登录状态。连续离线 90 秒后，先检查能否连接 `www.qq.com:443`，再尝试恢复在线状态。网络不可达时继续等待。上线失败后，只通过已认证的本机 `RestartNapCat` 接口重启机器人进程，用既有账号缓存登录。不执行全局 QQ 进程终止，不删除登录缓存，也不修改设备标识。

重启后等待 120 秒。若 NapCat 仍未使用缓存登录，提交一次指定机器人账号的快速登录请求。请求完成后等待在线确认。只有状态接口确认在线，才报告恢复成功。

配置项：

- `QQBOT_AUTO_RECOVERY=true`：在一键启动时启用。
- `QQBOT_RECOVERY_OFFLINE_SECONDS=90`：连续离线确认时间，最低 30 秒。
- `QQBOT_RECOVERY_RESTART_COOLDOWN=300`：两次重启至少间隔 300 秒，最低 120 秒。
- `QQBOT_RECOVERY_MAX_RESTARTS=3`：每小时最多三次重启，最大五次。
- `NAPCAT_UIN`：机器人 QQ 号。当前 NapCat 账号与配置不同，恢复进程停止操作。

计数和操作状态保存在 `runtime/private/napcat_connection.json`。恢复进程自身重启也保留次数限制。更新后的 `/api/health` 显示 `connection_recovery`。使用 `--no-napcat` 启动时不补起恢复进程。

被 QQ 踢下线（"登录已失效"等）时，同样先等 90 秒，再重启一次 NapCat，用缓存登录。这一次计入每小时重启上限。重启后 QQ 仍要求重新认证，或缓存登录没有上线，状态变为 `needs_authentication`，停止自动重启。账号认证完成、状态恢复在线后解除暂停。旧的“二维码已过期”文本本身不算凭据撤销。

限制：恢复进程不能替 QQ 完成安全验证。NapCat WebUI 无响应时会记录 `unreachable`，不会启动第二份 QQ。公网探测成功也不能证明 QQ 的所有网关正常。恢复机制处理网络中断后的失联，不保证消除 QQ 服务端的全部掉线原因。
