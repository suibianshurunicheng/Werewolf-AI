# strategy QLoRA 实测

状态：trained；epoch=1.0，step=1。
数据：dataset_v0.1；训练15，验证3。
PyTorch峰值分配显存：3315.8 MiB；验证Loss：3.058638。
最优验证Loss checkpoint：outputs/classic_v01/strategy/checkpoint-1。
非零LoRA B矩阵：252；相对上一阶段改变的张量数：504。

这里只证明真实SFT与保存成功。专项能力是否提升必须看相同Benchmark和语义审核，不能用Loss代替。
Adapter和optimizer等大文件留在本机outputs；迁移主机必须复制weights_location并校验artifacts.json中的SHA，Git仓库不含这些权重。
