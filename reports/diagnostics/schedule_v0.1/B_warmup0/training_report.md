# A vs B_warmup0 真实训练证据

三阶段完成且checkpoint逐文件SHA、实际张量变化、冻结计划LR均核验通过。能力结论待同23-dev全量语义复核。

|阶段|A/B optimizer步|A/B非零LR步|A valLoss|本组valLoss|本组trainLoss|峰值MiB|best step|
|---|---|---|---|---|---|---|---|
|rules|2/2|1/2|3.061335|2.971962|3.273305|3414.2|2|
|strategy|2/2|1/2|3.705309|3.491447|3.781560|3316.9|2|
|tactics|2/2|1/2|3.800267|3.568643|3.705547|3443.7|2|

## rules

A实际LR=[0.0, 5e-05]；本组实际LR=[5e-05, 2.5e-05]

initial Adapter：fresh LoRA on frozen Base; no prior adapter

final Adapter SHA：b7c6e157a5bcf722fac53aa88e0e6fcfdad5049d5d6d2c9c9d505bd1ba6894fc

best=outputs/diagnostics/schedule_v0.1/B_warmup0/rules/checkpoint-2；final=outputs/diagnostics/schedule_v0.1/B_warmup0/rules/final。final与best逐字节相同。

本阶段实际非零更新=2，best前缀非零更新=2。

## strategy

A实际LR=[0.0, 5e-05]；本组实际LR=[5e-05, 2.5e-05]

initial Adapter：outputs/diagnostics/schedule_v0.1/B_warmup0/rules/final

final Adapter SHA：ea4799d04f57919ac7d92ec23cd856b6f2db3bc8c1a2ae1049f782c0dc2cb287

best=outputs/diagnostics/schedule_v0.1/B_warmup0/strategy/checkpoint-2；final=outputs/diagnostics/schedule_v0.1/B_warmup0/strategy/final。final与best逐字节相同。

本阶段实际非零更新=2，best前缀非零更新=2。

## tactics

A实际LR=[0.0, 5e-05]；本组实际LR=[5e-05, 2.5e-05]

initial Adapter：outputs/diagnostics/schedule_v0.1/B_warmup0/strategy/final

final Adapter SHA：da5172fa95537b65a59c50e7edb603f96436dee051ed5de56daeadffda855777

best=outputs/diagnostics/schedule_v0.1/B_warmup0/tactics/checkpoint-2；final=outputs/diagnostics/schedule_v0.1/B_warmup0/tactics/final。final与best逐字节相同。

本阶段实际非零更新=2，best前缀非零更新=2。

## 限制与恢复

A的零LR步仍积累Adam动量。warmup变化也改变cosine轨迹和LR积分，不能只归因于计数。best选择依旧依赖很小的阶段验证集，尤其Tactics仅1条验证；Loss不是狼人杀能力验收。

完整config、数据SHA、Base revision、日志、每步train/val/epoch、checkpoint SHA、逐步张量变化见各阶段run_manifest、training.jsonl、artifacts和schedule_audit。大权重在outputs；Git只保存证据，迁移主机须复制并校验权重。已完成阶段不可重训。
