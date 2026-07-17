# Day 3–5 规则模型与黄金规则包交接说明

## 本阶段交付

本阶段在报账领域包内实现了安全、确定性、可追溯的规则内核，并手工编译了国内差旅、
会议费、IT维护支撑费正式报账三个候选规则包。代码没有修改 `QueryEngine`、工具注册器、
插件加载器或前端。规则内核不依赖聊天历史和模型输出；后续 OpenHarness Tool 只负责把
结构化事实交给该内核，再把结果映射为稳定响应。

主要文件：

- `rules/models.py`：规则、条件、来源清单和场景规则包的不可变 Schema；
- `rules/loader.py`：使用 `yaml.safe_load` 加载规则，限制文件类型、大小和符号链接；
- `rules/validators.py`：执行受控条件、核对来源、检测冲突并阻止未审批规则发布；
- `configs/finance/reimbursement_assistant/source_manifest.yaml`：外部财务资料的版本、状态
  和 SHA-256；不保存原始制度；
- `configs/finance/reimbursement_assistant/rule_packs/`：三个 `review_required` 候选包；
- `scripts/finance/validate_reimbursement_rules.py`：开发和 CI 使用的规则检查入口；
- `test_rule_models.py`、`test_golden_rule_packs.py`：安全语言、来源、冲突和业务分支测试。

## Harness 设计约束

规则包是 Harness 可调用的领域能力，不是提示词。当前只允许 `eq`、`in`、`exists`、
`gt`、`all`、`any` 六种操作符，且事实路径只能使用安全的点号字段名；YAML 中不能执行
Python。相同输入事实会得到相同的适用规则，便于 OpenHarness 会话恢复、回放、评测和
审计。加载器为每个包计算内容校验和并生成 `RulePackVersion`，以后每次工具响应都可记录
精确规则版本。

模型以后可以用于识别用户表达和抽取事实，但不能修改规则包、覆盖阻断结论或跳过来源
验证。规则包仍为只读数据；发布必须通过 Schema、来源、冲突、黄金集和人工批准。

## 第一步：复制本阶段代码

在 `feature/reimbursement-assistant-bootstrap` 分支、Day1–2提交之后应用交付补丁：

```bash
git apply --check finance_harness_day3_5.patch
git apply finance_harness_day3_5.patch
git status --short
```

如检查失败，请先核对当前提交是否为 Day1–2的 `a5dec26` 或其后继提交，不要强制覆盖。

## 第二步：安装依赖

```bash
uv sync --extra dev
```

本阶段新增 `types-PyYAML` 作为开发依赖，仅用于严格类型检查。运行时继续使用项目已有的
`PyYAML`。

## 第三步：验证候选规则

```bash
uv run python scripts/finance/validate_reimbursement_rules.py
```

预期输出三个 `VALID`，规则数量分别为国内差旅8、会议费10、IT维护支撑费10。
`publishable=False` 是当前正确结果，因为财务资料尚未完成版本和适用范围确认。

此时运行发布检查应返回非零退出码：

```bash
uv run python scripts/finance/validate_reimbursement_rules.py --require-publishable
test "$?" -eq 2
```

这证明候选包不会被误当作生产规则激活。

## 第四步：运行专项检查

```bash
uv run pytest -q tests/test_finance_harness/test_reimbursement_assistant
uv run ruff check \
  src/openharness/finance_harness/reimbursement_assistant \
  tests/test_finance_harness/test_reimbursement_assistant \
  scripts/finance
uv run mypy \
  src/openharness/finance_harness/reimbursement_assistant \
  scripts/finance
```

前端类型检查：

```bash
(cd frontend/terminal && npx tsc --noEmit)
```

完整上游回归沿用 Day1-2 的受控环境和命令执行。上游测试集中包含真实模型或真实外部服务调用；只有在密钥受控、费用可追踪且已确认测试数据允许外发的环境中，才执行 `uv run pytest -q`。Day3-5 的本地交付门槛以专项测试、Ruff、Mypy、规则发布门禁和前端类型检查为准。

## 第五步：财务复核

请财务接口人依据 `RULE_PACK_REVIEW_CHECKLIST.md` 检查三个场景边界、28条规则、例外条件、
提示语和来源定位。重点补齐成本费用域手册、预算流程和两份映射表的适用单位、生效日期和
审批结论。任何冲突都保留 `review_required`，并新增明确的冲突记录，禁止开发人员自行
选定答案。

完成审批后，更新来源清单的 `approval_status` 和必要的生效日期，再将经批准规则包改为
`active`、填写 `effective_date`，最后执行：

```bash
uv run python scripts/finance/validate_reimbursement_rules.py --require-publishable
```

只有退出码为0，规则包才具备进入后续只读 OpenHarness Tool 的条件。

## Day 3–5 完成判定

- 三个候选规则包100%通过Schema和来源完整性验证；
- 28条规则全部带文档版本、表格/行定位和SHA-256；
- 条件语言无任意代码执行能力；
- 来源缺失、校验和变化、规则冲突或未审批状态会阻止发布；
- 每个关键条件与例外都有自动化测试；
- 财务人工批准前，三个包保持 `review_required`；
- OpenHarness上游核心零修改。
