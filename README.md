# 🚀 量化因子回测系统 v2.0

基于TA-Lib的专业量化因子计算与回测框架，专为ETF/指数量化投资设计。

## ✨ 核心特性

- 🔧 **98个技术指标因子**：完整的TA-Lib因子库，涵盖动量、成交量、波动率、K线形态等
- 📊 **智能因子分析**：IC分析、因子排名、相关性分析
- 🎯 **多因子融合**：等权重、IC加权、LightGBM机器学习融合
- 🚀 **一键运行**：端到端自动化流程，从数据处理到结果输出
- 💾 **高性能缓存**：增量数据更新，智能缓存机制
- 🎛️ **灵活配置**：YAML配置文件，支持因子参数调优

## 🏗️ 项目架构

```
backtest_frame_v2/
├── 📁 engine/              # 核心计算引擎
│   ├── data_interface.py   # 统一数据接口
│   ├── factor_engine.py    # 因子计算引擎（98个因子）
│   ├── ic_engine.py        # IC分析引擎
│   ├── fusion_engine.py    # 因子融合引擎
│   └── factors/            # 因子实现库
│       ├── price_factors.py      # 价格因子
│       ├── momentum_factors.py   # 动量因子
│       ├── volume_factors.py     # 成交量因子
│       ├── pattern_factors.py    # K线形态因子
│       └── ...
├── 📁 pipelines/           # 流水线模块
│   ├── run_factors.py      # 因子计算流水线
│   ├── run_ic.py          # IC分析流水线
│   ├── run_fusion.py      # 因子融合流水线
│   └── test_pipeline.py   # 系统测试流水线
├── 📁 scripts/             # 工具脚本
├── 📁 config/              # 配置文件
│   ├── factors.yml         # 因子配置
│   └── universe_*.csv      # 标的池配置
├── 📁 data/                # 数据存储
├── 📁 reports/             # 输出报告
└── run_pipeline.py         # 主执行脚本
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install pandas numpy tushare talib pyyaml scikit-learn lightgbm

# 配置Tushare Token（可选，用于数据更新）
cp .env.template .env
# 编辑.env文件，填入你的TUSHARE_TOKEN
```

### 2. 一键运行

```bash
# 完整流程（因子计算 → IC分析 → 因子融合）
python run_pipeline.py

# 快速测试（推荐新手）
python run_pipeline.py test

# 单步运行
python run_pipeline.py factors  # 仅因子计算
python run_pipeline.py ic       # 仅IC分析
python run_pipeline.py fusion   # 仅因子融合
```

### 3. 结果查看

运行完成后，结果保存在`reports/`目录：

```
reports/
├── 📊 因子分析结果
│   ├── factor_ranking.csv      # 因子表现排名
│   ├── ic_timeseries.csv       # IC时间序列
│   ├── ic_summary.csv          # IC统计摘要
│   └── factors/                # 各因子详细数据
├── 🎯 融合结果
│   ├── fusion_equal_weight.csv # 等权融合因子
│   ├── fusion_ic_weight.csv    # IC加权融合因子
│   ├── fusion_lgb.csv          # LightGBM融合因子
│   └── fusion_weights.csv      # 融合权重
└── 📝 分析报告
    ├── factor_summary.txt      # 因子分析报告
    └── fusion_summary.txt      # 融合分析报告
```

## 📊 因子库概览

### 98个技术指标因子

| 分类 | 因子数量 | 代表因子 | 成功率 |
|------|----------|----------|--------|
| **价格因子** | 6个 | 收益率、对数收益率、价格相对位置 | 100% |
| **重叠研究** | 12个 | SMA、EMA、TEMA、KAMA、SAR | 100% |
| **动量指标** | 21个 | RSI、MACD、ADX、CMO、ROC | 100% |
| **成交量指标** | 5个 | OBV、Accumulation、Price Volume | 100% |  
| **波动率指标** | 15个 | ATR、布林带、NATR、TRANGE | 100% |
| **价格变换** | 12个 | WMA、MIDPRICE、TYPPRICE | 100% |
| **统计函数** | 9个 | 线性回归、标准差、方差、相关性 | 100% |
| **数学变换** | 9个 | SIN、COS、LOG、SQRT、TANH | 100% |
| **K线形态** | 9个 | 十字星、锤头、吞没、启明星 | 100% |

> **总成功率：98/98 = 100%** ✅

### 因子配置示例

```yaml
# config/factors.yml
factors:
  # 动量因子
  rsi14:
    enabled: true
    window: 14
    description: "14日RSI相对强弱指标"
    
  # K线形态因子
  cdl_doji:
    enabled: true
    description: "十字星形态"
    
  # 自定义参数
  macd_signal:
    enabled: true
    fast: 12
    slow: 26
    signal: 9
    description: "MACD信号线"
```

## 🔧 高级功能

### 1. 自定义因子

```python
# 在 engine/factors/ 中添加新因子
class CustomFactors(BaseFactor):
    def my_custom_factor(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """自定义因子实现"""
        return close.rolling(window).apply(lambda x: your_logic(x))
```

### 2. 因子融合策略

```python
from engine.fusion_engine import FusionEngine

fusion = FusionEngine()

# 等权重融合
equal_weights = fusion.equal_weight_fusion(factor_names)

# IC加权融合
ic_weights = fusion.ic_weight_fusion(ic_matrix)

# LightGBM融合
lgb_weights = fusion.lightgbm_fusion(factor_matrix, forward_returns)
```

### 3. IC分析

```python
from engine.ic_engine import ICEngine

ic_engine = ICEngine()

# 计算因子IC
ic_series = ic_engine.calc_ic_timeseries(factor, forward_returns)

# 生成IC报告
ic_report = ic_engine.generate_ic_report(ic_matrix)
```

## 🎯 应用场景

- **量化选股**：基于多因子模型进行股票/ETF筛选
- **因子研究**：技术指标的有效性分析和优化
- **策略开发**：多因子融合策略的构建和回测
- **风险管理**：因子暴露度分析和风险控制

## 📚 文档指南

详细文档请参考`docs/`目录：

- 📖 [**用户指南**](docs/USER_GUIDE.md) - 详细使用教程
- 🔧 [**因子使用指南**](docs/FACTOR_USAGE_GUIDE.md) - 98个因子的使用方法
- 🧪 [**测试指南**](docs/TEST_GUIDE.md) - 测试和调试方法
- 📊 [**TA-Lib因子库**](docs/COMPLETE_TALIB_FACTORS.md) - 完整因子列表
- 🔥 [**CDL因子修复报告**](docs/CDL_FACTOR_FIX_REPORT.md) - K线形态因子修复详情

## 🛠️ 技术特性

### 数据处理
- **智能缓存**：增量数据更新，避免重复下载
- **数据验证**：OHLC数据完整性检查和修复
- **格式统一**：自动处理不同数据源格式差异

### 计算优化
- **向量化计算**：基于NumPy/Pandas的高效计算
- **内存管理**：大数据集的分块处理机制
- **异常处理**：完善的错误处理和数值稳定性保证

### 结果输出
- **多格式支持**：CSV、Parquet等多种输出格式
- **可视化友好**：结构化输出，便于后续分析
- **详细日志**：完整的执行日志和错误跟踪

## 🔗 系统要求

- **Python**: 3.8+
- **操作系统**: Windows/macOS/Linux
- **内存**: 建议8GB+（处理大数据集）
- **存储**: 预留2GB+空间用于数据缓存

## 📝 更新日志

### v2.0.1 (2025-07-27)
- ✅ 修复CDL形态因子除零错误
- ✅ 完善标准化算法，处理离散值因子
- ✅ 优化因子参数传递机制
- ✅ 提升系统稳定性至100%

### v2.0.0
- 🎉 完整的98个TA-Lib技术指标实现
- 🚀 端到端自动化流程
- 📊 多因子融合功能
- 💾 智能数据缓存机制

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**量化因子回测系统 v2.0** - 让技术分析更简单，让量化投资更专业 🚀
