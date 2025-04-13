# 规划文档：BITZ Collector 客户端预估 Timing 过滤器

## 1. 目标

修改 `bitz collect` 命令的挖矿逻辑，增加一个基于客户端预估时间的过滤器。当客户端找到一个有效哈希解时，如果预估其在当前 Epoch 内的时间点已超过 30 秒，则放弃提交该解，以节省交易费用并避免提交大概率亏损的交易。

## 2. 核心逻辑

1.  **触发点**: 在 `find_hash_par` (或类似函数) 成功找到一个满足本地 `--min-difficulty` 的 `Solution` (包含 nonce, difficulty, hash) 之后，并且在调用 `send_and_confirm` (或负责提交交易的函数) 之前。
2.  **获取时间**:
    *   获取当前客户端系统时间 `T_found` (使用 `std::time::SystemTime::now()`)。
    *   获取当前 Epoch 的开始时间戳 `T_epoch_start` (秒级 Unix 时间戳)。
3.  **计算预估 Timing**:
    *   将 `T_found` 转换为秒级 Unix 时间戳 `ts_found`。
    *   计算 `estimated_timing = ts_found - T_epoch_start`。确保处理时间戳转换和计算中的潜在错误。
4.  **判断与执行**:
    *   **IF** `estimated_timing > 30`:
        *   记录日志: "Solution found (Difficulty: X) but estimated timing ({estimated_timing}s) > 30s. Skipping submission." (将 X 替换为实际难度)。
        *   **不**执行后续的交易准备和提交步骤。
        *   继续挖矿循环，寻找下一个解。
    *   **ELSE** (`estimated_timing <= 30`):
        *   按原有流程继续执行交易准备和提交 (`send_and_confirm`)。

## 3. 获取 Epoch 开始时间 (`T_epoch_start`) 的策略

*   **主要方法**:
    1.  调用 RPC 方法获取最新的区块信息 (例如 `getLatestBlockhash` 或 `getBlock`)，得到最新区块的时间戳 `ts_latest_block`。
    2.  从链上配置获取 Epoch 持续时间 `epoch_duration` (已知为 900 秒，但最好动态获取以防变化，可通过 `bitz program` 查看或直接调用 RPC 读取 BITZ Config 状态)。
    3.  计算 `T_epoch_start = floor(ts_latest_block / epoch_duration) * epoch_duration`。注意整数除法和取整。
*   **实现细节**:
    *   需要在 `utils/rpc.rs` 中可能添加新的辅助函数来封装获取最新区块时间和 BITZ Config 的逻辑。
    *   需要处理 RPC 调用可能失败的情况（例如返回错误、超时）。如果无法可靠获取 `T_epoch_start`，应考虑采取保守策略（例如，默认不进行过滤或记录错误并继续提交）。
*   **备选方法**: 检查是否有直接查询当前 Epoch 状态的 RPC 方法或链上账户。

## 4. 主要修改文件

*   **`src/command/mine.rs`**:
    *   在 `collect_solo` (和可能的 `collect_pool`，如果适用) 函数内，找到 `find_hash_par` 成功返回 `Solution` 后的位置。
    *   插入获取 `T_found`、调用获取 `T_epoch_start` 的逻辑、计算 `estimated_timing`、进行判断和日志记录的代码。
*   **`src/utils/rpc.rs`** (可能需要):
    *   添加获取最新区块时间戳的函数。
    *   添加获取 BITZ Config (包含 `epoch_duration`) 的函数。

## 5. 新增依赖

*   可能不需要新的外部 Crates，主要依赖 `std::time` 和现有的 `solana-client`。

## 6. 测试策略

*   **单元测试**: (如果可能) 测试计算 `T_epoch_start` 的逻辑。
*   **集成测试**: 运行 `bitz collect`，观察日志。
    *   验证在 Epoch 早期找到解时，是否能正常提交。
    *   通过模拟或其他方式（例如临时修改判断条件 `< 0` 来强制触发），验证在 `estimated_timing > 30` 时，是否会跳过提交并打印相应的日志。
    *   监控程序在长时间运行下的稳定性和资源使用情况。

## 7. 潜在风险与缓解

*   **Epoch 开始时间计算不准确**: 可能导致过滤行为不符合预期。缓解：仔细验证计算逻辑，添加日志记录 `ts_latest_block`, `epoch_duration`, `T_epoch_start` 以便调试。
*   **RPC 调用失败**: 可能导致无法执行过滤。缓解：添加错误处理，定义失败时的默认行为（例如打印警告日志并继续提交）。
*   **性能影响**: 频繁调用 RPC 获取区块时间可能略微增加开销。缓解：评估实际影响，考虑是否可以缓存 Epoch 开始时间（但要注意 Epoch 切换）。
