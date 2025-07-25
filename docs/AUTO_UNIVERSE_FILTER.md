# 自动化数据质量筛选使用说明

## 📋 概述

系统现在具备自动化数据质量筛选功能，会根据配置的数据区间和质量标准，自动从原始universe中筛选出高质量标的用于回测。

## 🔧 配置说明

### 基础配置
```yaml
# 数据配置
data:
  start_date: "20230101"
  end_date: "20250722"
  universe_file: "config/universe_local.csv"  # 只需配置原始universe文件
```

### 筛选参数配置
```yaml
# Universe质量筛选配置
universe_filter:
  enabled: true                # 是否启用自动筛选
  min_coverage_rate: 0.65      # 最低综合覆盖率（65%）
  min_close_coverage: 0.8      # 最低收盘价覆盖率（80%）  
  min_trading_days: 100        # 最少交易天数
  max_universe_size: 150       # 最大标的数量
  auto_update_days: 7          # 自动更新间隔（天）
```

## 🚀 自动化流程

### 1. 启动时自动检查
```
运行 run_factors.py 或 run_ic.py
    ↓
检查是否存在 universe_high_quality.csv
    ↓
如果不存在或过期（>7天），自动生成新的高质量universe
    ↓
使用高质量universe进行因子计算和IC分析
```

### 2. 筛选标准
- **数据完整性**：收盘价覆盖率 ≥ 80%
- **交易活跃度**：最少100个交易天数
- **综合质量**：整体数据覆盖率 ≥ 65%
- **数量控制**：最多选择150个高质量标的

### 3. 自动生成文件
- **输入**：`config/universe_local.csv`（原始universe）
- **输出**：`config/universe_high_quality.csv`（自动生成）
- **更新**：每7天自动检查并更新

## 📊 效果对比

### 使用前（全量universe）
```
标的数量: 248个
覆盖率: 2.49%
有效观测值: 22,752
```

### 使用后（自动筛选）
```
标的数量: 150个
覆盖率: 56-86%
有效观测值: 400,000+
```

## 💡 使用建议

### 1. 首次使用
- 确保 `config/universe_local.csv` 包含您要分析的所有标的
- 运行 `python pipelines/run_factors.py`，系统会自动生成高质量universe

### 2. 日常使用
- 直接运行因子计算或IC分析
- 系统会自动检查数据质量并使用最佳标的组合
- 无需手动干预

### 3. 自定义筛选标准
- 修改 `universe_filter` 配置参数
- 删除现有的 `universe_high_quality.csv` 文件
- 重新运行，系统会使用新标准生成

## 🔍 监控和调试

### 查看筛选日志
```bash
# 筛选过程会显示详细信息
[UniverseFilter] 原始标的数: 248
[UniverseFilter] 候选标的数: 237
[UniverseFilter] 最终选择数: 150
[UniverseFilter] 平均质量评分: 1.000
```

### 手动重新生成
```bash
# 删除现有文件，强制重新生成
rm config/universe_high_quality.csv
python pipelines/run_factors.py
```

## ⚠️ 注意事项

1. **文件优先级**：系统优先使用 `universe_high_quality.csv`，如果不存在则使用原始文件
2. **更新频率**：默认7天检查一次，可通过 `auto_update_days` 配置
3. **数据依赖**：确保 `data/processed/` 目录包含足够的历史数据
4. **配置简化**：无需在配置文件中指定高质量universe文件名，系统自动管理

## 🎯 最佳实践

1. **定期维护**：定期检查原始universe，添加新标的或移除不活跃标的
2. **参数调优**：根据数据质量情况调整筛选参数
3. **性能监控**：关注因子覆盖率和IC质量的变化
4. **备份重要**：定期备份高质量universe文件用于历史对比
