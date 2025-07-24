# 🚀 量化因子框架测试指南

## 快速测试

### 1. 完整流程测试（推荐）
```bash
# 运行端到端测试，最适合新手验证系统
python pipelines/test_pipeline.py

# 或者通过主脚本运行测试模式
python run_pipeline.py test
```

### 2. 生产环境运行
```bash
# 完整生产流程（处理全部标的池）
python run_pipeline.py

# 单独步骤调试
python run_pipeline.py factors    # 仅因子计算
python run_pipeline.py ic         # 仅IC分析  
python run_pipeline.py fusion     # 仅因子融合
```

### 3. 数据管理测试
```bash
# 测试智能缓存（首次会下载数据）
python scripts/build_data_warehouse.py

# 测试增量更新（第二次运行会使用缓存）
python scripts/build_data_warehouse.py

# 强制刷新测试
python scripts/build_data_warehouse.py --force
```

## 测试流程详解

完整测试包含以下 6 个核心步骤：

### 1. **引擎初始化** 
- 初始化数据接口、因子引擎、IC引擎、融合引擎
- 验证配置文件和数据路径
- 预计用时: < 0.1秒

### 2. **因子计算**
- 计算6种技术因子：`mom20`, `shortrev5`, `vol20`, `turn_mean20`, `amihud20`, `macd_signal`
- 基于13个核心标的，861个交易日数据
- 预计用时: 1-2秒

### 3. **IC分析** 
- 计算各因子与前瞻收益(5日)的信息系数
- 生成IC时间序列、滚动统计、相关性矩阵
- 预计用时: 0.5-1秒

### 4. **因子融合**
- 等权融合和IC加权融合
- 基于历史IC表现计算动态权重
- 预计用时: 0.5秒

### 5. **融合验证**
- 验证融合因子的IC表现
- 与单因子表现对比分析
- 预计用时: 0.3秒

### 6. **结果保存**
- 自动保存所有分析报告和因子数据
- 生成详细的统计摘要
- 预计用时: 0.2秒

**总预期用时**: 2.6-4秒

## 📊 输出文件详解

### 核心报告文件 (`reports/`)
- `ic_summary.csv` - IC汇总统计（均值、标准差、IR比率等）
- `factor_ranking.csv` - 因子表现排名（按IR排序）
- `ic_timeseries.csv` - IC时间序列数据
- `ic_rolling_mean.csv` - IC滚动均值（20日窗口）
- `ic_rolling_std.csv` - IC滚动标准差（20日窗口）
- `ic_correlation.csv` - 因子间相关性矩阵
- `fusion_weights.csv` - IC加权融合的动态权重
- `fusion_summary.txt` - 融合结果文字总结

### 因子数据文件 (`reports/factors/`)
- `mom20.csv` - 20日动量因子（价格相对强度）
- `shortrev5.csv` - 5日短期反转因子（短期均值回归）
- `vol20.csv` - 20日波动率因子（收益率标准差）
- `turn_mean20.csv` - 20日平均换手率（流动性指标）
- `amihud20.csv` - Amihud流动性因子（价格冲击成本）
- `macd_signal.csv` - MACD信号因子（技术分析指标）
- `fusion_equal_weight.csv` - 等权融合因子
- `fusion_ic_weight.csv` - IC加权融合因子
- `all_factors.parquet` - 所有因子的Parquet格式存储

## 🎯 典型测试结果

基于当前测试环境（13个核心标的，861个交易日，2022-2025数据）：

### 因子表现排行
1. **shortrev5** (短期反转) - IC≈0.020, IR≈0.096 ⭐
2. **turn_mean20** (换手率) - IC≈0.014, IR≈0.082
3. **vol20** (波动率) - IC≈0.012, IR≈0.075
4. **amihud20** (流动性) - IC≈0.008, IR≈0.045
5. **mom20** (动量) - IC≈0.005, IR≈0.025
6. **macd_signal** (MACD) - IC≈0.003, IR≈0.018

### 系统性能指标
- **数据规模**: 13标的 × 861交易日 = 11,193条记录
- **处理速度**: 完整流程2.6秒
- **内存占用**: < 100MB
- **磁盘占用**: 约15MB（含所有报告）

### 缓存性能测试
```bash
# 首次运行（需要下载）
✅ 000001.SH 从API获取数据... (861天, 2022-01-04~2025-07-24) [3.2s]

# 第二次运行（使用缓存）  
✅ 000001.SH 使用缓存数据 (861天, 2022-01-04~2025-07-24) [0.1s]
```

**缓存命中率**: 通常 > 95%，大幅减少API调用

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 数据相关问题
```bash
# 问题：数据缺失或过时
# 解决：重新构建数据仓库
python scripts/build_data_warehouse.py --force

# 问题：标的池为空
# 解决：检查标的池文件
cat config/universe_small.csv | wc -l  # 应该 > 10

# 问题：API令牌无效
# 解决：检查.env配置
cat .env | grep TUSHARE_TOKEN
```

#### 2. 性能问题
```bash
# 问题：处理速度过慢
# 检查：数据规模是否合理
python -c "import pandas as pd; print(pd.read_csv('config/universe_small.csv').shape)"

# 问题：内存不足
# 解决：使用更小的标的池进行测试
python scripts/filter_universe.py --target_type index --index_type main
```

#### 3. 权限和路径问题
```bash
# 检查目录权限
ls -la reports/ data/

# 确保必要目录存在
mkdir -p reports/factors logs data/processed
```

### 数据状态检查命令

```bash
# 检查数据文件状态
find data/processed -name "*.parquet" | wc -l

# 检查最近的日志
tail -20 logs/data_build.log

# 验证因子配置
python -c "import yaml; print(yaml.safe_load(open('config/factors.yml')))"

# 检查API连接
python -c "import tushare as ts; import os; from dotenv import load_dotenv; load_dotenv(); print('API OK' if ts.pro_api(os.getenv('TUSHARE_TOKEN')) else 'API Error')"
```

## 🚀 性能优化建议

### 针对不同使用场景

1. **快速验证** (< 5秒)
   ```bash
   # 使用预设的13个核心标的
   python pipelines/test_pipeline.py
   ```

2. **中等规模测试** (< 30秒)
   ```bash
   # 筛选100-200个主要标的
   python scripts/filter_universe.py --target_type both --etf_type main --index_type main
   python run_pipeline.py
   ```

3. **大规模分析** (几分钟)
   ```bash
   # 使用完整标的池进行生产级分析
   # 建议先确保系统资源充足
   python scripts/filter_universe.py --target_type both --etf_type all --index_type all
   python run_pipeline.py
   ```

## 📈 下一步发展

测试成功后，框架已具备以下扩展能力：

### 即将支持的功能
1. **vectorbt回测引擎集成** - 完整的历史回测
2. **实时信号生成** - 基于最新数据的交易信号
3. **风险管理模块** - 组合风险评估和控制
4. **可视化仪表板** - Web界面的实时监控

### 技术扩展方向
1. **更多因子类型** - 基本面、情绪、宏观因子
2. **机器学习增强** - 非线性因子挖掘
3. **多频率分析** - 日内、周度、月度因子
4. **跨资产分析** - 股票、期货、期权联动

---
*最后更新: 2025年7月25日*
