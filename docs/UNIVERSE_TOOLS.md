# 标的池管理工具使用说明

## 工具概述

本项目提供两个主要的标的池管理工具：

1. **update_universe.py**: 获取所有ETF和指数，保存到 `config/universe.csv`
2. **filter_universe.py**: 从完整标的池中筛选符合条件的标的，导出到指定文件

## 使用流程

### 1. 获取完整标的池

```bash
# 获取所有ETF和指数（包括SSE、SZSE、CSI、CNI）
python scripts/update_universe.py
```

这将获取约8000+个标的（2245个ETF + 5837个指数），保存到 `config/universe.csv`

### 2. 筛选合适的标的

```bash
# 筛选主要ETF和指数
python scripts/filter_universe.py --target_type both --etf_type main --index_type main --output universe_main.csv

# 筛选所有ETF
python scripts/filter_universe.py --target_type etf --etf_type all --output etf_all.csv

# 筛选主要指数
python scripts/filter_universe.py --target_type index --index_type main --output index_main.csv
```

## 筛选参数说明

### filter_universe.py 参数

- `--target_type`: 目标类型
  - `etf`: 只筛选ETF
  - `index`: 只筛选指数  
  - `both`: 筛选ETF和指数（默认）

- `--etf_type`: ETF类型
  - `main`: 主要ETF（过滤掉货币、债券ETF）
  - `all`: 所有ETF

- `--index_type`: 指数类型
  - `main`: 主要指数（9个核心宽基指数）
  - `all`: 所有指数

- `--min_list_days`: 最小上市天数，默认365天

- `--output`: 输出文件名，默认 `universe_filtered.csv`

## 使用示例

```bash
# 获取完整标的池
python scripts/update_universe.py

# 筛选适合分析的主要标的
python scripts/filter_universe.py --target_type both --etf_type main --index_type main --output universe_analysis.csv

# 筛选长期稳定的ETF
python scripts/filter_universe.py --target_type etf --etf_type main --min_list_days 1095 --output etf_stable.csv
```

## 当前配置

项目当前使用 `config/universe_small.csv`（13个核心标的）进行测试和分析，包括：
- 9个主要指数：上证指数、沪深300、中证500等  
- 4个主要ETF：50ETF、300ETF、500ETF等

如需使用其他标的池，修改 `scripts/build_data_warehouse.py` 中的 `universe_file` 变量即可。
