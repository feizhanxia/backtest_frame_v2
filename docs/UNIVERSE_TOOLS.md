# 📋 标的池管理工具使用说明

## 工具概述

本项目提供完整的标的池管理解决方案，包含两个核心工具：

1. **update_universe.py**: 从Tushare获取所有ETF和指数，构建完整标的池
2. **filter_universe.py**: 基于多种条件智能筛选，生成分析用标的池

## 🚀 使用流程

### 第一步：获取完整标的池

```bash
# 获取所有ETF和指数（包括SSE、SZSE、CSI、CNI等交易所）
python scripts/update_universe.py
```

**预期结果**:
- 获取约8000+个标的（约2245个ETF + 5837个指数）
- 保存至 `config/universe.csv`
- 包含完整的基础信息（代码、名称、类型、分类）

### 第二步：智能筛选标的

```bash
# 🎯 推荐配置：筛选主要ETF和核心指数
python scripts/filter_universe.py --target_type both --etf_type main --index_type main

# 📊 其他常用配置
python scripts/filter_universe.py --target_type etf --etf_type all --output etf_all.csv
python scripts/filter_universe.py --target_type index --index_type main --output index_main.csv
```

## 🔧 筛选参数详解

### filter_universe.py 核心参数

| 参数 | 选项 | 说明 | 推荐使用 |
|-----|------|------|---------|
| `--target_type` | `etf` / `index` / `both` | 标的类型选择 | `both` |
| `--etf_type` | `main` / `all` | ETF筛选强度 | `main` |
| `--index_type` | `main` / `all` | 指数筛选强度 | `main` |
| `--output` | 文件名 | 输出文件名称 | `universe_small.csv` |

### ETF筛选逻辑 (`--etf_type`)

#### `main` 模式（推荐）
**过滤掉的类型**:
- 货币类ETF：`货币`、`短债`、`中债`、`长债`
- 债券类ETF：`债券`、`可转债`、`国债`
- 特殊类ETF：`REITs`、`QDII`、`商品`、`黄金`、`原油`、`白银`

**保留的类型**：股票型ETF、行业ETF、主题ETF等

#### `all` 模式
保留所有ETF，无过滤

### 指数筛选逻辑 (`--index_type`)

#### `main` 模式（推荐）
**仅保留9个核心宽基指数**:
- `000001.SH` - 上证指数
- `000300.SH` - 沪深300
- `000905.SH` - 中证500  
- `000852.SH` - 中证1000
- `399001.SZ` - 深证成指
- `399006.SZ` - 创业板指
- `000688.SH` - 科创50
- `000016.SH` - 上证50
- `932000.CSI` - 中证2000

#### `all` 模式  
保留所有指数（5000+个）

## 💡 使用示例

### 基础操作
```bash
# 1️⃣ 获取完整标的池（首次使用必须）
python scripts/update_universe.py

# 2️⃣ 快速生成分析用标的池（推荐新手）
python scripts/filter_universe.py --target_type both --etf_type main --index_type main

# 3️⃣ 验证筛选结果
head -5 config/universe_small.csv
wc -l config/universe_small.csv
```

### 进阶配置
```bash
# 🎯 专注股票ETF分析
python scripts/filter_universe.py --target_type etf --etf_type main --output stock_etf.csv

# 📊 指数对比分析
python scripts/filter_universe.py --target_type index --index_type main --output core_indices.csv

# 🔍 全市场ETF分析（包含特殊类型）
python scripts/filter_universe.py --target_type etf --etf_type all --output all_etf.csv
```

### 批量处理
```bash
# 生成多个不同用途的标的池
python scripts/filter_universe.py --target_type both --etf_type main --index_type main --output analysis_pool.csv
python scripts/filter_universe.py --target_type etf --etf_type main --output etf_pool.csv  
python scripts/filter_universe.py --target_type index --index_type all --output index_pool.csv
```

## 📊 筛选效果统计

### 典型筛选结果（基于8082个原始标的）

| 配置 | ETF数量 | 指数数量 | 总数量 | 用途 |
|-----|---------|----------|--------|------|
| `both + main + main` | 2174 | 9 | 2183 | 🎯 日常分析 |
| `etf + main` | 2174 | 0 | 2174 | 📈 ETF专项 |
| `index + main` | 0 | 9 | 9 | 📊 指数对比 |
| `etf + all` | ~2245 | 0 | ~2245 | 🔍 全ETF分析 |

### 过滤统计示例
```text
=== 过滤结果统计 ===
原始标的数量: 8082
有效标的数量: 2183  
失败标的数量: 5899

失败原因统计:
非主要指数          5828
过滤掉货币/债券ETF      43  
过滤掉特殊类型ETF       28
```

## ⚡ 性能优化特点

### 处理速度
- **原版本**: 需要API验证，8000+标的需要数小时
- **优化版本**: 纯本地筛选，8000+标的 < 1秒
- **处理速度**: > 100,000 标的/秒

### 稳定性改进
- ❌ **移除了**: API调用、网络依赖、超时风险  
- ✅ **保留了**: 基础信息筛选、名称过滤、类型分类
- 🚀 **新增了**: 批量处理、统计报告、错误跟踪

## 🔄 与数据流程集成

### 标准工作流
```bash
# 步骤1: 更新标的池（月度更新）
python scripts/update_universe.py

# 步骤2: 筛选分析标的（根据需要）
python scripts/filter_universe.py --target_type both --etf_type main --index_type main

# 步骤3: 构建数据仓库（使用筛选后的标的池）
python scripts/build_data_warehouse.py

# 步骤4: 执行因子分析
python run_pipeline.py
```

### 自定义标的池使用
```bash
# 生成自定义标的池后，修改build_data_warehouse.py中的配置
# 将 universe_file = "universe_small.csv" 改为你的文件名
```

## 📁 当前项目配置

### 默认标的池
- **文件**: `config/universe_small.csv`
- **规模**: 2183个标的（2174个ETF + 9个指数）
- **用途**: 系统测试和日常分析
- **更新**: 可通过重新运行筛选脚本更新

### 切换标的池
```python
# 在 scripts/build_data_warehouse.py 中修改：
universe_file = "universe_small.csv"      # 当前默认
# universe_file = "your_custom_pool.csv"  # 切换到自定义
```

---
*最后更新: 2025年7月25日*
