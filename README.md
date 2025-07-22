# 🚀 量化因子分析框架 v2.0

这是一个模块化、高效、可扩展的量化因子分析和回测框架，支持多源数据接入、多因子计算、IC分析、因子融合及未来的回测验证。

## 📋 项目概览

### 核心目标
构建一个**模块化、高效、可扩展**的量化因子分析框架，支持：
- 多源数据接入与标准化处理
- 多类型因子计算与验证
- 因子有效性分析（IC分析）
- 多因子融合策略
- 回测验证与性能评估（待开发）

### 技术架构
- **数据层**: Parquet存储 + 无前视偏差对齐
- **因子层**: 模块化因子计算引擎 + 标准化流程
- **分析层**: IC分析引擎 + 多因子融合引擎
- **回测层**: vectorbt集成（待开发）
- **配置层**: YAML配置驱动 + 灵活参数管理

### 设计原则
- **模块化**: 引擎独立，职责单一
- **可配置**: YAML驱动，无硬编码
- **高性能**: Parquet存储，vectorized计算
- **可扩展**: 支持新因子、新融合方法
- **生产级**: 错误处理，日志记录，性能优化

## 📁 项目结构

```
backtest_frame_v2/
├── config/                     # 配置文件
│   ├── factors.yml            # 因子配置（启用/参数）
│   └── universe.csv           # 股票池配置
├── data/                      # 数据存储
│   ├── raw/                   # 原始数据
│   ├── processed/YYYY/        # Parquet分区数据
│   └── cache/                 # 缓存数据
├── engine/                    # 核心引擎
│   ├── data_interface.py      # 数据访问接口
│   ├── factor_engine.py       # 因子计算引擎
│   ├── ic_engine.py          # IC分析引擎
│   ├── fusion_engine.py      # 因子融合引擎
│   ├── data_fetcher.py       # 数据获取
│   ├── aligner.py            # 数据对齐
│   ├── cleaner.py            # 数据清洗
│   └── storage.py            # 存储管理
├── pipelines/                 # 执行流水线
│   ├── test_pipeline.py      # 完整流程测试
│   ├── run_factors.py        # 因子计算
│   ├── run_ic.py             # IC分析
│   └── run_fusion.py         # 因子融合
├── scripts/                   # 工具脚本
│   ├── build_data_warehouse.py  # 数据仓库构建
│   └── update_universe.py       # 股票池更新
├── reports/                   # 分析报告输出
│   ├── factors/              # 因子数据
│   ├── ic_summary.csv        # IC统计
│   └── factor_ranking.csv    # 因子排名
├── run_pipeline.py           # 主运行脚本
├── README.md                 # 项目说明
└── TEST_GUIDE.md             # 测试指南
```

## 🔧 安装与配置

### 1. 安装依赖
```bash
pip install pandas numpy pyarrow tushare tqdm matplotlib pyyaml scikit-learn
```

### 2. 配置 Tushare API（可选）
如果需要获取最新数据，请创建`.env`文件，填入您的Tushare API Token：
```
TUSHARE_TOKEN=your_token_here
```

### 3. 股票池配置
默认使用`config/universe.csv`中的股票池，可通过以下命令更新：
```bash
# 获取沪深300成分股
python scripts/update_universe.py

# 也可以自定义参数
# 中证500成分股
python scripts/update_universe.py --index_code 000905.SH
```

### 4. 因子配置
编辑`config/factors.yml`文件来启用/禁用因子或调整参数：
```yaml
factors:
  mom20:
    enabled: true    # 开启/关闭因子
    window: 20       # 参数配置
```

## 🚀 快速开始

### 1. 数据准备
```bash
# 构建数据仓库（首次使用必须运行）
python scripts/build_data_warehouse.py
```

### 2. 运行测试（推荐新用户）
```bash
# 运行完整测试流程
python pipelines/test_pipeline.py
```

### 3. 完整分析流程
```bash
# 一键完成全流程
python run_pipeline.py

# 或分步执行
python run_pipeline.py factors    # 仅计算因子
python run_pipeline.py ic         # 仅进行IC分析
python run_pipeline.py fusion     # 仅进行因子融合
python run_pipeline.py test       # 运行测试流程
```

## 📊 核心功能

### 1. 数据处理
- **无前视偏差**: 严格按照公布日期对齐财务数据
- **数据清洗**: 缺失值处理、去极值、标准化
- **高效存储**: Parquet分区存储，增量更新，指纹检测

### 2. 因子计算
当前支持的因子类型：
- **动量因子**: `mom20` (20日动量)
- **反转因子**: `shortrev5` (5日短期反转)
- **波动率因子**: `vol20` (20日波动率)
- **流动性因子**: `turn_mean20` (20日换手率), `amihud20` (流动性)

### 3. IC分析
- **相关性分析**: Spearman相关系数，前瞻收益率相关性
- **统计指标**: IC均值、IC_IR、胜率、相关性矩阵
- **滚动分析**: 滚动IC均值和标准差

### 4. 因子融合
支持的融合策略：
- **等权融合**: 简单平均权重
- **IC加权融合**: 基于IC_IR的动态权重
- **LightGBM融合**: 机器学习融合（框架已实现）

## 🔍 设计思想

### 模块化设计
每个引擎独立，职责单一，便于扩展和维护：
```python
data_interface = DataInterface()      # 数据访问
factor_engine = FactorEngine()        # 因子计算  
ic_engine = ICEngine()                # IC分析
fusion_engine = FusionEngine()        # 因子融合
```

### 配置驱动
通过YAML配置驱动，无硬编码，灵活调整：
```yaml
# factors.yml - 配置因子参数
factors:
  mom20:
    enabled: true
    window: 20
```

### 数据流设计
清晰的数据处理流程：
```
原始数据 → 清洗对齐 → Parquet存储 → 因子计算 → IC分析 → 因子融合 → 回测验证
```

### 高性能优化
- **多线程并发**: 使用`ThreadPoolExecutor`加速数据获取
- **缓存机制**: 交易日索引缓存，减少重复计算
- **增量更新**: 只获取最新数据，与本地数据拼接
- **向量化计算**: 避免循环，使用pandas矢量操作

## 📈 当前状态与结果

### 数据规模
- **股票数量**: 300只股票
- **时间范围**: 858个交易日（2022至今）

### 因子表现
当前测试结果：
- **最佳单因子**: `shortrev5` (IC=0.0204, IR=0.0955)
- **次佳因子**: `turn_mean20` (IC=0.0141, IR=0.0822)
- **融合表现**: 等权融合与IC加权融合均已实现

### 框架状态
- **数据模块**: 100% 完成
- **因子模块**: 100% 完成
- **分析模块**: 100% 完成
- **融合模块**: 100% 完成
- **回测模块**: 0% 待开发

## 💡 使用案例

### 添加新因子
在`engine/factor_engine.py`中添加计算函数：
```python
def calculate_new_factor(self, price_data, fin_data=None):
    """计算新因子"""
    # 实现因子计算逻辑
    return factor_df
```

并在`config/factors.yml`中添加配置：
```yaml
factors:
  new_factor:
    enabled: true
    parameter1: value1
```

### 自定义融合策略
在`engine/fusion_engine.py`中添加新的融合方法：
```python
def custom_fusion(self, ic_df):
    """自定义融合策略"""
    # 实现融合逻辑
    return weights
```

## 🛠️ 故障排除

### 常见问题
1. **数据缺失**: 确保已运行 `build_data_warehouse.py`
2. **权限错误**: 检查目录权限
3. **运行错误**: 查看详细错误日志

### 数据验证
检查数据完整性：
```bash
# 检查数据文件
ls -la data/processed/2025/

# 检查股票池
cat config/universe.csv | wc -l

# 验证无前视偏差
python -c "import pandas as pd; df=pd.read_parquet('data/processed/2025/07/*.parquet'); print(f'前视行数: {df[df.index < df.get(\"pub_date\", df.index)].shape[0]}')"
```

## 🔜 下一步计划

### 回测引擎开发
- vectorbt 集成
- 多空策略实现
- 性能评估指标

### 策略模块
- 基于因子分位数的选股策略
- 多因子组合优化
- 动态调仓策略

### 可视化与报告
- 交互式图表
- HTML/PDF报告生成

## 📝 贡献指南

欢迎贡献新的因子、融合方法或其他改进！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

---

*如需更多详细说明，请参阅 TEST_GUIDE.md 获取测试相关信息。*

*最后更新: 2025年7月22日*
