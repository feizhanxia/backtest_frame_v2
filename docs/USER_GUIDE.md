# 量化回测框架使用指南

## 📊 项目架构总览

```
backtest_frame_v2/
├── 🏗️ 核心引擎 (engine/)
│   ├── data_fetcher.py      # 数据获取引擎 (支持增量更新)
│   ├── data_interface.py    # 数据访问接口 (统一数据访问)
│   ├── factor_engine.py     # 因子计算引擎 (6种技术因子)
│   ├── ic_engine.py         # IC分析引擎 (因子有效性)
│   ├── fusion_engine.py     # 因子融合引擎 (多因子策略)
│   ├── storage.py           # 数据存储工具
│   └── universe_filter.py   # 高级标的池筛选
│
├── 🔄 流水线 (pipelines/)
│   ├── run_factors.py       # 因子计算流水线
│   ├── run_ic.py            # IC分析流水线
│   ├── run_fusion.py        # 因子融合流水线
│   └── test_pipeline.py     # 系统测试流水线
│
├── 🛠️ 工具脚本 (scripts/)
│   ├── update_universe.py   # 获取最新标的池
│   ├── build_data_warehouse.py # 批量下载数据
│   ├── local_universe.py    # ETF跟踪指数提取
│   └── filter_universe.py   # 基础标的池筛选
│
├── ⚡ 一键运行
│   ├── run_pipeline.py      # 完整自动化流程
│   ├── test.ipynb           # 交互式测试
│   └── README.md            # 项目文档
```

## 🚀 使用流程

### 1. 环境准备
```bash
# 安装依赖
pip install pandas numpy pyarrow tushare tqdm matplotlib pyyaml scikit-learn lightgbm python-dotenv

# 配置API
cp .env.template .env
# 编辑 .env 文件，填入您的 TUSHARE_TOKEN
```

### 2. 数据准备 (两种方式)

#### 方式A: 获取完整标的池
```bash
# 1. 获取8000+标的列表
python scripts/update_universe.py

# 2. 筛选有效标的
python scripts/filter_universe.py --target_type both

# 3. 批量下载数据
python scripts/build_data_warehouse.py
```

#### 方式B: 使用ETF跟踪指数
```bash
# 从ETF文件提取跟踪指数代码
python scripts/local_universe.py
```

### 3. 因子分析 (三种运行方式)

#### 一键运行 (推荐)
```bash
python run_pipeline.py
```

#### 分步运行
```bash
# 1. 计算因子
python pipelines/run_factors.py

# 2. IC分析
python pipelines/run_ic.py

# 3. 因子融合
python pipelines/run_fusion.py
```

#### 交互式分析
```bash
# 使用Jupyter Notebook
jupyter notebook test.ipynb
```

### 4. 系统测试
```bash
# 运行完整测试
python pipelines/test_pipeline.py
```

## 📈 因子说明

### 技术因子 (6种)
- **mom20**: 20日动量因子 - 价格趋势
- **shortrev5**: 5日短期反转 - 短期回调
- **vol20**: 20日波动率 - 价格波动性
- **macd_signal**: MACD信号 - 趋势确认
- **turn_mean20**: 20日换手率 - 流动性代理
- **amihud20**: Amihud流动性 - 市场流动性

### 数据处理流程
```
原始数据 → 前向填充(5天) → 分位截断(1%-99%) → Z-score标准化
```

## 📋 输出报告

### 因子报告 (reports/)
- `factor_summary.txt` - 因子生成统计
- `factors/` - 各因子明细数据

### IC分析报告
- `ic_summary.csv` - IC统计摘要
- `ic_timeseries.csv` - IC时间序列
- `ic_correlation.csv` - 因子相关性
- `factor_ranking.csv` - 因子排名

### 融合策略报告
- `fusion_summary.txt` - 融合策略统计
- `fusion_equal_weight.csv` - 等权重融合
- `fusion_ic_weight.csv` - IC加权融合
- `fusion_weights.csv` - 融合权重

## ⚙️ 配置管理

### 主配置文件: config/factors.yml
```yaml
# 数据配置
data:
  start_date: "20230101"
  end_date: "20250722"
  universe_file: "config/universe_local.csv"

# 因子配置
factors:
  mom20:
    enabled: true
    window: 20
  # ... 其他因子

# 预处理配置
preprocessing:
  max_days: 5
  quantiles: [0.01, 0.99]
```

### 标的池配置: config/universe_local.csv
```csv
ts_code
000001.SH
000002.SH
...
```

## 🔧 高级功能

### 数据质量筛选
```python
from engine.universe_filter import UniverseFilter

# 自动筛选高质量标的
filter = UniverseFilter()
high_quality_universe = filter.generate_high_quality_universe(
    min_coverage=0.8,
    min_trading_days=200
)
```

### 自定义因子计算
在 `engine/factor_engine.py` 中添加新因子：
```python
def my_custom_factor(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """自定义因子计算"""
    return close.rolling(window).apply(lambda x: custom_logic(x))
```

## 📊 性能特性

- **智能缓存**: 基于哈希比对的增量数据更新
- **高效筛选**: 8000+标的快速筛选 (<1秒)  
- **快速测试**: 完整测试流程 2.6秒
- **存储优化**: Parquet格式，50%存储节省

## 🚨 注意事项

1. **数据对齐**: 系统使用交集对齐，确保所有标的同时有数据
2. **时序安全**: 严格防止未来数据泄露，因子T vs 收益T+1
3. **内存管理**: 大规模数据分批处理，避免内存溢出
4. **错误处理**: 完善的异常处理和日志记录

## 📞 技术支持

- 项目结构清晰，模块化设计
- 完整的错误处理和日志系统
- 支持增量更新和断点续传
- 兼容多种数据源格式
