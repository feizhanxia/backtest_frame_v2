# 🚀 量化因子框架测试指南

## 快速测试

### 1. 完整流程测试
```bash
# 运行完整的端到端测试（推荐）
python pipelines/test_pipeline.py

# 或者通过主脚本运行
python run_pipeline.py test
```

### 2. 分步骤运行
```bash
# 完整流程（生产模式）
python run_pipeline.py

# 单独步骤
python run_pipeline.py factors    # 仅因子计算
python run_pipeline.py ic         # 仅IC分析
python run_pipeline.py fusion     # 仅因子融合
```

## 测试内容

完整测试包含以下 6 个步骤：

1. **引擎初始化** - 初始化所有核心引擎
2. **因子计算** - 计算启用的技术因子
3. **IC分析** - 计算各因子与前瞻收益的相关性
4. **因子融合** - 等权和IC加权融合
5. **融合验证** - 验证融合因子的有效性
6. **结果保存** - 保存所有分析报告

## 输出文件

### 报告文件 (`reports/`)
- `ic_summary.csv` - IC汇总统计
- `factor_ranking.csv` - 因子表现排名
- `ic_timeseries.csv` - IC时间序列
- `ic_correlation.csv` - 因子相关性矩阵
- `fusion_weights.csv` - 融合权重

### 因子数据 (`reports/factors/`)
- `mom20.csv` - 20日动量因子
- `shortrev5.csv` - 5日短期反转因子
- `vol20.csv` - 20日波动率因子
- `turn_mean20.csv` - 20日平均换手率
- `amihud20.csv` - Amihud流动性因子
- `fusion_equal_weight.csv` - 等权融合因子
- `fusion_ic_weight.csv` - IC加权融合因子

## 预期结果

基于当前数据（300支股票，858个交易日），典型的测试结果：

- **最佳单因子**: `shortrev5` (IC≈0.020, IR≈0.096)
- **次佳因子**: `turn_mean20` (IC≈0.014, IR≈0.082)  
- **总用时**: 约5-8秒
- **数据规模**: 858×300的因子矩阵

## 故障排除

### 常见问题
1. **数据缺失**: 确保已运行 `python scripts/build_data_warehouse.py`
2. **权限错误**: 确保 `reports/` 目录可写
3. **内存不足**: 当前数据规模较小，一般不会有问题

### 检查数据状态
```bash
# 检查数据文件
ls -la data/processed/2025/

# 检查股票池
cat config/universe.csv | wc -l

# 检查因子配置
cat config/factors.yml
```

## 下一步

测试成功后，框架已可用于：
1. 开发 vectorbt 回测引擎
2. 策略信号生成模块
3. 回测验证与性能评估

---
*更新时间: 2025年7月22日*
