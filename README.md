# ETF/指数量化因子分析框架 v2.0

该项目提供一套简单的因子分析流程，专注于ETF/指数的技术面研究。

## 主要特性
- 数据获取与清洗
- 多种技术因子计算
- IC 分析与因子融合
- 自动生成分析报告

## 快速开始
```bash
# 安装依赖
pip install pandas numpy pyarrow tushare tqdm matplotlib pyyaml scikit-learn lightgbm

# 构建数据（首次运行）
python scripts/build_data_warehouse.py

# 执行完整流程
python run_pipeline.py
```

典型的终端输出如下：
```text
🚀 量化因子回测系统 v2.0
步骤 1/3: 因子计算
步骤 2/3: IC 分析
步骤 3/3: 因子融合
🎉 完成！
```

更多测试与进阶用法请参考 [TEST_GUIDE.md](./TEST_GUIDE.md)。

## 贡献
欢迎通过 Pull Request 提交改进或新功能。
