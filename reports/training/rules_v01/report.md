# rules QLoRA 实测

状态：trained；epoch=1.0，step=3。
数据：dataset_v0.1；训练35，验证7。
PyTorch峰值分配显存：3376.9 MiB；验证Loss：2.968798。
最优验证Loss checkpoint：outputs/classic_v01/rules/checkpoint-3。
非零LoRA B矩阵：252；相对上一阶段改变的张量数：首阶段。

这里只证明真实SFT与保存成功。专项能力是否提升必须看相同Benchmark和语义审核，不能用Loss代替。
Adapter和optimizer等大文件留在本机outputs；迁移主机必须复制weights_location并校验artifacts.json中的SHA，Git仓库不含这些权重。
