# ETF/指数量化因子分析框架 v2.0

专为ETF和指数设计的轻量级量化因子分析框架，具备智能缓存、自动化数据管理和完整的因子分析流程。

## ✨ 主要特性 (已优化)

- **智能数据管理**: 基于哈希比对的增量更新，避免重复下载，50%存储节省
- **多标的支持**: 支持ETF和指数的自动识别与处理  
- **完整因子分析**: 6种技术因子计算、IC分析、因子融合，2.6秒完整测试
- **高效标的池**: 从8000+标的中快速筛选(<1秒)，无API调用卡顿
- **自动报告生成**: 一键生成完整的分析报告和可视化结果

## 🚀 快速开始

### 环境准备
```bash
# 安装依赖
pip install pandas numpy pyarrow tushare tqdm matplotlib pyyaml scikit-learn lightgbm python-dotenv

# 配置Tushare API
cp .env.template .env
# 编辑 .env 文件，填入您的 TUSHARE_TOKEN
```

### 标的池管理
```bash
# 1. 获取完整标的池（8000+标的）
python scripts/update_universe.py

# 2. 筛选适合分析的标的（推荐）
python scripts/filter_universe.py --target_type both --etf_type main --index_type main
```

### 数据构建
```bash
# 构建数据仓库（自动缓存，支持增量更新）
python scripts/build_data_warehouse.py

# 强制刷新所有数据
python scripts/build_data_warehouse.py --force
```

### 执行分析
```bash
# 完整分析流程
python run_pipeline.py

# 快速测试（推荐新手）
python pipelines/test_pipeline.py
```

典型的终端输出：
```text
🚀 量化因子回测系统 v2.0
✅ 引擎初始化完成
✅ 因子计算完成 (6个因子)
✅ IC分析完成 (IR≈0.096)  
✅ 因子融合完成 (等权+IC加权)
✅ 结果保存完成
🎉 测试完成，总用时: 2.6秒
```

## 📊 系统架构

### 数据流程
```
原始数据(Tushare) → 缓存检查 → 数据清洗 → 因子计算 → IC分析 → 因子融合 → 报告生成
```

### 核心引擎
- **DataFetcher**: 智能数据获取，支持缓存与增量更新
- **FactorEngine**: 6种技术因子计算（动量、反转、波动率等）
- **ICEngine**: IC分析与统计检验
- **FusionEngine**: 多种因子融合策略

## 📁 目录结构

```
backtest_frame_v2/
├── config/                    # 配置文件
│   ├── factors.yml           # 因子配置
│   ├── universe.csv          # 完整标的池 (8000+)
│   └── universe_small.csv    # 筛选后标的池 (2000+)
├── engine/                   # 核心引擎
│   ├── data_fetcher.py      # 智能数据获取
│   ├── factor_engine.py     # 因子计算引擎
│   ├── ic_engine.py         # IC分析引擎
│   └── fusion_engine.py     # 因子融合引擎
├── scripts/                  # 工具脚本
│   ├── update_universe.py   # 标的池更新
│   ├── filter_universe.py   # 标的池筛选
│   └── build_data_warehouse.py # 数据仓库构建
├── data/                     # 数据存储
│   └── processed/           # 清洗后的数据
└── reports/                 # 分析报告
    ├── factors/             # 因子数据
    └── *.csv               # 各种分析结果
```

## 🛠️ 进阶使用

详细的使用指南请参考：
- [测试指南](./docs/TEST_GUIDE.md) - 完整的测试流程和故障排除
- [标的池工具](./docs/UNIVERSE_TOOLS.md) - 标的池管理和筛选指南

## 📈 性能特点

- **数据规模**: 支持2022-2025年历史数据（3.5年，800+交易日）
- **处理速度**: 2000+标的完整分析 < 10秒
- **缓存优化**: 智能缓存减少90%重复下载
- **内存优化**: 批量处理，支持大规模数据集

## 🤝 贡献

欢迎通过 Pull Request 提交改进建议：
- 新的技术因子实现
- 性能优化方案  
- 文档完善
- Bug修复

---
*最后更新: 2025年7月25日*
