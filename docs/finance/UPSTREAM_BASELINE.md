# OpenHarness 基线冻结记录（Day 1–2）

## 1. 已确认的信息

本次设计审阅使用 OpenHarness 官方源码提交
`9b2efd795c6aa09f88b0c257d269a9e518da6ae7`（项目版本 0.1.9）作为接口参考。
该提交只用于核对 `BaseTool`、项目插件发现和测试工具链，不代表开发者真实仓库当前提交。

上传的《财务Harness代码说明》记录了以下项目状态：

- 目标仓库：`~/projects/harness/OpenHarness`；
- Python 3.11、uv、Node.js 20；
- 计划工作分支：`feature/reimbursement-assistant-bootstrap`；
- 上一阶段记录的完整回归：1154 passed、6 skipped，Ruff 和 TypeScript 检查通过；
- `finance_harness/reimbursement_assistant` 已有目录、基础 Schema 和参考文档枚举，尚无业务逻辑闭环。

以上内容来自说明文档，合入代码前必须在真实仓库重新采集，不能直接当作当前测试结果。

## 2. 需要在真实仓库生成的本地记录

在仓库根目录运行：

```bash
python scripts/finance/capture_reimbursement_baseline.py \
  --output docs/finance/UPSTREAM_BASELINE.local.md \
  --run-checks
```

脚本会记录分支、提交、Git 状态、工具版本、领域测试、Ruff、Mypy、完整 Pytest 和
前端 TypeScript 检查。它不会读取环境变量、用户名、主机名或业务文档。生成后核对：

1. 当前分支是 `feature/reimbursement-assistant-bootstrap`；
2. 合入 Day 1–2 文件前已保存原有未提交修改；
3. `git rev-parse HEAD` 与团队锁定的基准提交一致；
4. 失败项已区分为环境问题、已有问题和本次新增问题；
5. 冲刺期间不合并新的上游 `main`。

## 3. Day 1–2 变更边界

允许新增报账助手领域 Schema、配置示例、合成验收契约、ADR、基线脚本和测试。
本阶段不修改 QueryEngine、默认 ToolRegistry、UI、权限框架或上游插件加载器，也不激活
任何未经财务复核的业务规则。

## 4. 本次隔离环境验证结果

在官方参考提交的隔离副本中叠加本交付后，验证结果如下：

- 报账助手目标测试：34 passed；
- Ruff：通过；
- 严格 Mypy：通过；
- OpenHarness 完整回归：1184 passed、1 failed、6 skipped；
- 单独复跑失败项仍失败：
  `test_agent_send_message_flow_restarts_completed_agent`，属于未修改的上游任务进程测试；
- 前端 `npx tsc --noEmit`：通过。

完整回归使用可写的临时 HOME 并清除了沙箱代理变量。唯一失败项与本次新增领域文件没有依赖
关系，但真实开发机仍需按项目锁定的 Python 3.11、Node.js 20 和实际提交重新执行。本隔离
环境为 Python 3.12、Node.js 24，结果只作为交付自检记录。

## 5. 复现命令

```bash
uv run pytest -q tests/test_finance_harness/test_reimbursement_assistant
uv run ruff check \
  src/openharness/finance_harness/reimbursement_assistant \
  tests/test_finance_harness/test_reimbursement_assistant \
  scripts/finance/capture_reimbursement_baseline.py
uv run mypy \
  src/openharness/finance_harness/reimbursement_assistant \
  scripts/finance/capture_reimbursement_baseline.py
uv run pytest -q
(cd frontend/terminal && npx tsc --noEmit)
```
