# 🚀 ETF/指数量化因子分析框架 v2.0

一个**模块化、高效、可扩展**的量化因子分析框架，专注于ETF/指数技术面分析。

## ✨ 核心特性

- **📊 完整流程**: 数据获取 → 因子计算 → IC分析 → 因子融合 → 报告生成
- **⚡ 高性能**: Parquet存储 + 向量化计算，完整流程仅需2.4秒
- **🎯 专业分析**: 6大技术因子，3种融合策略，20+分析报告
- **� 易于使用**: YAML配置驱动，一键运行，模块化设计

## � 快速开始

### 安装运行
```bash
# 1. 安装依赖
pip install pandas numpy pyarrow tushare tqdm matplotlib pyyaml scikit-learn lightgbm

# 2. 构建数据（首次运行）
python scripts/build_data_warehouse.py

# 3. 运行分析
python run_pipeline.py
```

### 运行结果
```
🚀 量化因子回测系统 v2.0
================================================================================
🔄 步骤 1/3: 因子计算 - 因子矩阵形状: (859, 36)
🔄 步骤 2/3: IC分析 - 最佳因子: mom20 (IC_IR: 0.092)  
🔄 步骤 3/3: 因子融合 - 等权融合: ✅ IC加权融合: ✅
🎉 完整流程执行成功！⏱️ 总耗时: 2.4 秒
```

## 📊 核心功能详解

### 🗄️ 数据处理能力
- **🔄 多源数据支持**: ETF/指数/股票数据，Tushare API集成
- **🧹 智能数据清洗**: 缺失值处理、极值检测、标准化
- **⚡ 高效存储**: Parquet列式存储，压缩率90%+，读取速度10x提升
- **🔄 增量更新**: 智能增量更新，避免重复下载
- **📅 数据对齐**: 自动处理交易日对齐、时区处理

### 🧮 技术因子体系
当前实现**6大类技术因子**，专注ETF/指数择时分析：

| 因子类别 | 因子名称 | 计算逻辑 | 适用场景 |
|---------|----------|----------|----------|
| **📈 动量因子** | `mom20` | 20日收益率 | 趋势跟踪、动量策略 |
| **🔄 反转因子** | `shortrev5` | 5日反转强度 | 短期回归、反转策略 |
| **📊 波动率因子** | `vol20` | 20日收益波动率 | 风险管理、波动率策略 |
| **💧 流动性因子** | `turn_mean20` | 20日平均换手率 | 流动性分析 |
| **💰 冲击成本** | `amihud20` | Amihud流动性指标 | 交易成本评估 |
| **🔧 技术指标** | `macd_signal` | MACD信号线 | 技术分析、择时 |

### 📈 IC分析引擎
全面的因子有效性评估：

#### 核心指标体系
```python
# IC统计指标
ic_mean        # IC均值：衡量因子预测方向
ic_std         # IC标准差：衡量因子稳定性  
ic_ir          # 信息比率：IC均值/IC标准差
win_rate       # 胜率：IC>0的比例
abs_ic_mean    # 绝对IC均值：衡量因子强度
```

#### 滚动分析
- **📊 60日滚动IC**: 短期表现跟踪
- **📈 全历史IC**: 长期稳定性评估
- **🔗 因子相关性**: 多因子去重分析

### 🧠 因子融合策略
支持多种科学的因子融合方法：

#### 1. 等权融合 (Equal Weight)
```python
weight_i = 1/N  # 简单平均，适合探索阶段
```

#### 2. IC加权融合 (IC Weighted)  
```python
weight_i = |IC_mean_i| / Σ|IC_mean_j|  # 基于历史IC表现
```

#### 3. 机器学习融合 (LightGBM)
```python
# 使用梯度提升学习因子间非线性关系
model = LightGBMRegressor(
    objective='regression',
    metric='mse', 
    boosting_type='gbdt'
)
```

### 📋 报告体系
生成**20+个分析文件**，全方位评估：

#### 因子分析报告
- `factors/all_factors.parquet`: 完整因子矩阵
- `factor_ranking.csv`: 因子表现排名
- `factor_summary.txt`: 统计摘要

#### IC分析报告  
- `ic_timeseries.csv`: IC时间序列
- `ic_summary.csv`: IC统计指标
- `ic_correlation.csv`: 因子相关性矩阵

#### 融合结果报告
- `fusion_equal_weight.csv`: 等权融合结果
- `fusion_ic_weight.csv`: IC加权融合结果  
- `fusion_summary.txt`: 融合统计摘要

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

## 🎯 当前项目状态

### 📊 数据规模统计
- **🎯 标的池规模**: 2,202个ETF/指数（可配置筛选）
- **📅 时间覆盖**: 859个交易日（2022-01-01至2025-07-22）
- **💾 数据存储**: 原始数据 + Parquet压缩存储
- **🔄 更新频度**: 支持实时增量更新

### 🏆 因子表现排名
基于最新分析结果（IC_IR 60日滚动）：

| 排名 | 因子名称 | IC_IR_60d | 绝对IC均值 | 胜率 | 综合得分 | 性能评级 |
|-----|----------|-----------|------------|------|----------|----------|
| 🥇 1 | **mom20** | **0.092** | 0.433 | 48.2% | **0.739** | ⭐⭐⭐⭐⭐ |
| 🥈 2 | **shortrev5** | 0.004 | 0.430 | 49.0% | 0.547 | ⭐⭐⭐⭐ |
| 🥉 3 | **vol20** | 0.032 | 0.419 | 47.4% | 0.508 | ⭐⭐⭐ |
| 4 | amihud20 | -0.063 | 0.364 | 53.8% | 0.412 | ⭐⭐⭐ |
| 5 | turn_mean20 | -0.068 | 0.330 | 52.2% | 0.225 | ⭐⭐ |
| 6 | macd_signal | -0.027 | 0.345 | 49.0% | 0.222 | ⭐⭐ |

### 📈 系统性能指标
- **⚡ 执行速度**: 完整流程 2.4秒
- **💾 存储效率**: Parquet压缩率 90%+
- **📊 数据覆盖**: 因子覆盖率 97%+
- **🎯 计算精度**: 浮点数完整精度保持

### 🔧 模块完成度
```
✅ 数据模块      100% │ ████████████████████
✅ 因子模块      100% │ ████████████████████  
✅ IC分析模块    100% │ ████████████████████
✅ 融合模块      100% │ ████████████████████
✅ 报告模块      100% │ ████████████████████
🔄 回测模块        0% │ ░░░░░░░░░░░░░░░░░░░░ (规划中)
```

### 📁 输出文件统计
当前系统生成 **20个分析文件**：
- **📊 因子数据**: 7个文件（Parquet + CSV格式）
- **📈 IC分析**: 6个文件（时间序列 + 统计摘要）
- **🧠 融合结果**: 4个文件（多策略融合）
- **📝 统计报告**: 3个文件（可读性报告）

### 🎨 可视化能力
- **📊 因子表现**: IC时间序列图表
- **🔗 相关性**: 因子相关性热力图
- **📈 融合效果**: 权重分布可视化
- **📋 综合报告**: 结构化文本报告

## 💡 进阶使用指南

### 🔧 自定义因子开发

#### 1. 添加新因子
在`engine/factor_engine.py`中新增计算函数：

```python
def calculate_custom_factor(self, price_data: Dict[str, pd.DataFrame], **params) -> pd.DataFrame:
    """
    自定义因子计算模板
    
    Args:
        price_data: 价格数据字典 {symbol: DataFrame}
        **params: 因子参数（从config/factors.yml读取）
    
    Returns:
        pd.DataFrame: 因子值矩阵 (dates × symbols)
    """
    window = params.get('window', 20)
    result_list = []
    
    for symbol, df in price_data.items():
        # 实现您的因子计算逻辑
        factor_values = df['close'].rolling(window).apply(your_custom_logic)
        result_list.append(factor_values.rename(symbol))
    
    return pd.concat(result_list, axis=1)
```

#### 2. 配置文件注册
在`config/factors.yml`中添加配置：

```yaml
factors:
  custom_factor:
    enabled: true
    window: 20
    param1: value1
    param2: value2
    description: "自定义因子说明"
```

### 🧠 自定义融合策略

#### 1. 扩展融合引擎
在`engine/fusion_engine.py`中添加新策略：

```python
def risk_parity_fusion(self, factor_data: pd.DataFrame, ic_summary: pd.DataFrame) -> Dict[str, float]:
    """
    风险平价融合策略
    基于因子波动率的风险平价权重分配
    """
    factor_vol = factor_data.std()  # 计算因子波动率
    inv_vol = 1 / factor_vol        # 波动率倒数
    weights = inv_vol / inv_vol.sum()  # 标准化权重
    
    return weights.to_dict()

def momentum_fusion(self, ic_df: pd.DataFrame, lookback: int = 60) -> Dict[str, float]:
    """
    IC动量融合策略  
    基于IC动量分配权重
    """
    recent_ic = ic_df.tail(lookback).mean()  # 近期IC均值
    positive_ic = recent_ic[recent_ic > 0]   # 只保留正IC
    weights = positive_ic / positive_ic.sum() if len(positive_ic) > 0 else {}
    
    return weights.to_dict()
```

### 📊 自定义分析指标

#### 1. 扩展IC分析
添加新的因子评估指标：

```python
# 在 engine/ic_engine.py 中添加
def calculate_advanced_metrics(self, ic_df: pd.DataFrame) -> pd.DataFrame:
    """计算高级IC指标"""
    metrics = {}
    
    for factor in ic_df.columns:
        ic_series = ic_df[factor].dropna()
        
        # 新增指标
        metrics[factor] = {
            'ic_skew': ic_series.skew(),           # IC偏度
            'ic_kurtosis': ic_series.kurtosis(),   # IC峰度  
            'max_drawdown': self._calc_max_drawdown(ic_series.cumsum()),
            'sharpe_ratio': ic_series.mean() / ic_series.std() * np.sqrt(252),
            'calmar_ratio': ic_series.mean() / abs(metrics[factor]['max_drawdown'])
        }
    
    return pd.DataFrame(metrics).T
```

### 🎯 性能优化技巧

#### 1. 数据处理优化
```python
# 使用向量化操作替代循环
# ❌ 低效方式
for symbol in symbols:
    result[symbol] = data[symbol].rolling(20).mean()

# ✅ 高效方式  
result = data.rolling(20).mean()  # pandas 自动向量化
```

#### 2. 内存优化
```python
# 数据类型优化
df = df.astype({
    'close': 'float32',      # 降低精度节省内存
    'volume': 'uint32',      # 使用无符号整型
    'symbol': 'category'     # 分类数据使用category
})

# 分块处理大数据
def process_large_data(data, chunk_size=1000):
    for chunk in pd.read_csv(data, chunksize=chunk_size):
        yield process_chunk(chunk)
```

#### 3. 并行计算
```python
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

# CPU密集型任务使用进程池
with mp.Pool(processes=mp.cpu_count()) as pool:
    results = pool.map(calculate_factor, data_chunks)

# I/O密集型任务使用线程池
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(fetch_data, symbol) for symbol in symbols]
```

## 🛠️ 故障排除与调试

### 🚨 常见问题与解决方案

#### 1. 数据相关问题
```bash
# ❌ 问题：数据文件缺失
ERROR: 找不到数据文件 data/processed/2025/07/*.parquet

# ✅ 解决方案
python scripts/build_data_warehouse.py  # 重新构建数据仓库
```

```bash
# ❌ 问题：Tushare API超限
ERROR: 抱歉，您每分钟最多访问该接口200次

# ✅ 解决方案
# 1. 等待1分钟后重试
# 2. 或使用现有数据：python run_pipeline.py（跳过数据更新）
```

#### 2. 配置相关问题
```bash
# ❌ 问题：因子配置错误
KeyError: 'enabled' in factors.yml

# ✅ 解决方案：检查YAML格式
factors:
  mom20:
    enabled: true  # 确保布尔值格式正确
    window: 20     # 确保数值类型正确
```

#### 3. 性能相关问题
```bash
# ❌ 问题：运行缓慢
运行时间 > 10秒

# ✅ 解决方案
# 1. 减少标的数量：编辑 config/universe.csv
# 2. 禁用耗时因子：在 factors.yml 中设置 enabled: false
# 3. 使用缓存数据：避免重复数据构建
```

### 🔍 数据验证命令

#### 验证数据完整性
```bash
# 📊 检查数据文件数量
find data/processed -name "*.parquet" | wc -l

# 📅 检查时间范围
python -c "
import pandas as pd
import glob
files = glob.glob('data/processed/2025/07/*.parquet')
if files:
    df = pd.read_parquet(files[0])
    print(f'时间范围: {df.index.min()} 至 {df.index.max()}')
    print(f'交易日数量: {len(df)}')
"

# 🎯 检查标的数量
python -c "
import pandas as pd
universe = pd.read_csv('config/universe.csv')
print(f'标的池大小: {len(universe)} 个')
print(f'标的类型分布: {universe["target_type"].value_counts()}')
"
```

#### 验证因子质量
```bash
# 🧮 检查因子数据
python -c "
import pandas as pd
factors = pd.read_parquet('reports/factors/all_factors.parquet')
print(f'因子矩阵形状: {factors.shape}')
print(f'缺失值比例: {factors.isnull().sum().sum() / factors.size:.2%}')
print(f'因子列表: {list(factors.columns.get_level_values(0).unique())}')
"

# 📈 检查IC质量
python -c "
import pandas as pd
ic_summary = pd.read_csv('reports/ic_summary.csv', index_col=0)
print('IC统计摘要:')
print(ic_summary[['ic_mean_full', 'ic_ir_full', 'win_rate']].round(4))
"
```

### 📋 调试模式使用

#### 1. 详细日志输出
```bash
# 开启详细模式
python run_pipeline.py --verbose

# 查看具体日志
tail -f logs/data_build.log       # 数据构建日志
tail -f logs/universe_update.log  # 标的池更新日志
```

#### 2. 分步调试
```bash
# 🔧 仅测试数据接口
python -c "
from engine.data_interface import DataInterface
di = DataInterface()
price_data = di.load_price_data()
print(f'数据加载成功: {price_data.shape}')
"

# 🧮 仅测试因子计算
python -c "
from pipelines.run_factors import main
main()
print('因子计算完成')
"
```

#### 3. 性能分析
```bash
# ⏱️ 模块耗时分析
python -m cProfile -s cumulative run_pipeline.py > profile_output.txt
head -20 profile_output.txt  # 查看最耗时的函数
```

### 💾 数据恢复与备份

#### 数据备份
```bash
# 📦 完整数据备份
tar -czf backup_$(date +%Y%m%d).tar.gz data/ reports/ logs/

# 🗜️ 仅备份处理后数据
tar -czf processed_data_backup.tar.gz data/processed/
```

#### 数据恢复
```bash
# 🔄 从备份恢复
tar -xzf backup_20250724.tar.gz

# 🏗️ 重建数据（如果备份不可用）
rm -rf data/processed/
python scripts/build_data_warehouse.py
```

### 🧪 测试环境设置

#### 创建测试配置
```bash
# 📝 创建测试专用配置
cp config/factors.yml config/factors_test.yml

# 编辑测试配置（减少数据量）
# factors_test.yml 中设置更小的时间范围和标的数量
```

#### 运行回归测试
```bash
# 🧪 完整测试套件
python pipelines/test_pipeline.py

# 📊 单元测试（如果可用）
python -m pytest tests/ -v
```

## 🔜 项目发展规划

### 🎯 Phase 2: 回测引擎开发 (Q4 2025)
- **📈 策略回测**: 
  - vectorbt 深度集成
  - 多空策略实现  
  - 动态调仓策略
  - 风险管理模块

- **📊 性能评估**:
  - 夏普比率、最大回撤
  - 信息比率、卡尔玛比率
  - 胜率、盈亏比统计
  - 基准比较分析

### 🚀 Phase 3: 策略优化 (Q1 2026)
- **🧠 因子挖掘**:
  - 基本面因子扩展
  - 高频技术因子
  - 情绪因子集成
  - 另类数据因子

- **⚙️ 参数优化**:
  - 遗传算法优化
  - 贝叶斯优化
  - 集合方法
  - 强化学习

### 📱 Phase 4: 可视化增强 (Q2 2026)
- **🎨 交互式图表**:
  - Plotly/Dash 集成
  - 实时数据看板
  - 策略监控面板
  - 风险预警系统

- **📄 报告自动化**:
  - HTML/PDF 报告
  - 邮件自动发送
  - 微信/钉钉推送
  - API 接口开放

### 🌐 Phase 5: 云端部署 (Q3 2026)
- **☁️ 云端架构**:
  - Docker 容器化
  - Kubernetes 编排
  - 微服务架构
  - API Gateway

- **� 实时数据**:
  - WebSocket 实时数据
  - Redis 缓存加速
  - 消息队列处理
  - 分布式计算

## 🤝 参与贡献

### 🎉 欢迎贡献
我们欢迎各种形式的贡献：
- **🐛 Bug 修复**: 发现并修复问题  
- **✨ 新功能**: 添加新因子、新策略
- **📝 文档完善**: 改进文档和示例
- **🧪 测试用例**: 增加测试覆盖
- **🎨 界面优化**: 改进用户体验

### 📋 贡献流程
1. **🍴 Fork 项目** → 创建个人分支
2. **🔧 本地开发** → 进行功能开发  
3. **🧪 测试验证** → 确保功能正常
4. **📝 文档更新** → 更新相关文档
5. **🔄 提交 PR** → 创建 Pull Request

### 🎯 贡献建议
当前最需要的贡献领域：

#### 🧮 因子开发
```python
# 示例：添加技术指标因子
def calculate_rsi_factor(self, price_data, window=14):
    """RSI 相对强弱指标"""
    # 实现 RSI 计算逻辑
    return rsi_values

def calculate_bollinger_factor(self, price_data, window=20, std_dev=2):
    """布林带指标"""  
    # 实现布林带计算逻辑
    return bollinger_values
```

#### 🧠 融合策略
```python
# 示例：添加机器学习融合
def xgboost_fusion(self, factor_data, target_returns):
    """XGBoost 因子融合"""
    import xgboost as xgb
    # 实现 XGBoost 融合逻辑
    return fusion_weights

def neural_network_fusion(self, factor_data, target_returns):
    """神经网络因子融合"""
    # 实现深度学习融合逻辑
    return fusion_weights
```

### 🏆 贡献者荣誉
感谢所有为项目做出贡献的开发者！

| 贡献者 | 主要贡献 | 提交数 |
|--------|----------|--------|
| [@feizhanxia](https://github.com/feizhanxia) | 项目创建者，核心架构设计 | 50+ |
| *等待您的参与!* | | |

## 📞 联系与支持

### 💬 技术交流
- **📧 邮箱**: [项目邮箱]
- **💬 微信群**: [二维码]
- **🔗 QQ群**: [群号]
- **📱 钉钉群**: [群号]

### 🐛 问题反馈
- **GitHub Issues**: [提交Bug报告](https://github.com/feizhanxia/backtest_frame_v2/issues)
- **功能请求**: [提交功能建议](https://github.com/feizhanxia/backtest_frame_v2/issues/new)
- **使用问题**: [讨论区提问](https://github.com/feizhanxia/backtest_frame_v2/discussions)

### 📚 学习资源
- **📖 量化金融**: [推荐书籍清单]
- **🎓 在线课程**: [学习路径推荐]  
- **📄 学术论文**: [因子模型相关论文]
- **💻 开源项目**: [相关项目推荐]

---

## 📝 更新日志

### v2.0.0 (2025-07-24) - 当前版本
- ✅ **完整框架重构**: 模块化设计，性能优化
- ✅ **6大技术因子**: 动量、反转、波动、流动性因子
- ✅ **IC分析引擎**: 完整统计指标，滚动分析
- ✅ **多策略融合**: 等权、IC加权、LightGBM融合
- ✅ **结构化报告**: 20+分析文件，全方位评估
- ✅ **日志系统**: 集中式日志管理

### v1.x.x (2025-07) - 历史版本
- 🔄 初始股票因子分析框架
- 🔄 基础数据获取和处理
- 🔄 简单IC分析实现

---

**🎯 项目愿景**: 打造业界领先的量化因子分析平台，让每个量化研究者都能便捷地进行因子挖掘和策略开发。

**📅 最后更新**: 2025年7月24日  
**🏷️ 当前版本**: v2.0.0  
**📊 项目状态**: 🟢 积极维护中

*感谢您使用 ETF/指数量化因子分析框架！如有任何问题或建议，欢迎随时联系我们。*
