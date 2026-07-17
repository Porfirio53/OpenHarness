# Day 1–2 操作与交接说明

## 交付结果

本阶段已完成基线采集脚本、系统边界 ADR、报账助手扩展 Schema、参考资料标识、配置安全
默认值、20 条合成验收合同和自动化合同测试。尚未实现分类器、规则加载器、状态机和
OpenHarness Tool；这些属于后续阶段。

## 第一步：在真实仓库确认现场

```bash
cd ~/projects/harness/OpenHarness
test "$(pwd)" = "$HOME/projects/harness/OpenHarness" || exit 1
git status --short
git branch --show-current
git rev-parse HEAD
```

如果存在未提交修改，先确认归属并保存；不要覆盖同名文件。当前分支应为
`feature/reimbursement-assistant-bootstrap`。如分支尚未创建，按照团队已约定的基线分支
创建，避免从最新 `main` 临时起步。

## 第二步：合入 Day 1–2 代码

优先使用交付的补丁：

```bash
git apply --check finance_harness_day1_2.patch
git apply finance_harness_day1_2.patch
git status --short
```

`git apply --check` 失败时先阅读冲突，不要使用强制覆盖。重点检查 `schemas.py`、
`reference_catalog.py` 和已有配置是否包含团队自己的未提交修改。

## 第三步：生成真实基线

```bash
uv sync --extra dev
python scripts/finance/capture_reimbursement_baseline.py \
  --output docs/finance/UPSTREAM_BASELINE.local.md \
  --run-checks
```

打开生成文件，记录实际提交、分支和失败命令。完整测试耗时较长时可以先不加
`--run-checks` 生成元数据，再在当天完成带检查的最终版本。

## 第四步：人工确认范围和用例

依次阅读：

1. `docs/finance/adr/0001-reimbursement-assistant-boundaries.md`；
2. `docs/finance/REIMBURSEMENT_ASSISTANT_ACCEPTANCE.md`；
3. `data/synthetic_finance/reimbursement_assistant/acceptance/day1_2_e2e_cases.jsonl`。

请组长或财务接口人确认三个 MVP 场景、预算/资金闸门、条件材料和安全回退。任何制度冲突
记录为待确认项，不在代码里自行选择答案。

## 第五步：运行验收

```bash
uv run pytest -q tests/test_finance_harness/test_reimbursement_assistant
uv run ruff check \
  src/openharness/finance_harness/reimbursement_assistant \
  tests/test_finance_harness/test_reimbursement_assistant \
  scripts/finance/capture_reimbursement_baseline.py
uv run mypy \
  src/openharness/finance_harness/reimbursement_assistant \
  scripts/finance/capture_reimbursement_baseline.py
```

随后检查完整回归和前端：

```bash
uv run pytest -q
(cd frontend/terminal && npx tsc --noEmit)
```

## 第六步：提交

确认 Git 中没有公司制度原文、真实附件、账号、截图、凭据或本地私有路径。检查无误后：

```bash
git add \
  src/openharness/finance_harness \
  configs/finance/reimbursement_assistant.example.yaml \
  data/synthetic_finance/reimbursement_assistant \
  docs/finance \
  scripts/finance/capture_reimbursement_baseline.py \
  tests/test_finance_harness/test_reimbursement_assistant
git diff --cached --check
git commit -m "feat(finance): freeze reimbursement assistant contracts"
```

## Day 1–2 完成判定

- 真实仓库提交、分支、工具版本和全量回归已记录；
- ADR 经开发负责人确认，三个 MVP 场景无新增范围；
- Schema 测试与 20 条合同校验通过；
- OpenHarness 上游核心没有改动；
- 财务规则争议已有负责人和确认时间；
- Day 3 可以直接开始 `rules/models.py`、加载器、校验器和三个黄金规则包。
