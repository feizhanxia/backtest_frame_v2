# 量化回测框架 - 数据模块

这是一个用于量化交易回测的数据获取和处理框架。该框架设计用于从Tushare获取股票数据，进行清洗、对齐和标准化处理，最后存储为高效的Parquet格式。

## 项目结构

```
quant_proj/
├─ config/
│   └─ universe.csv          # 股票池 ts_code 列，一行一个
├─ data/
│   ├─ raw/                  # 原始拉取（可删除）
│   └─ processed/YYYY/MM/    # 清洗后 Parquet 分区
├─ engine/
│   ├─ data_fetcher.py       # ⬇️ 拉取
│   ├─ aligner.py            # 🔄 对齐 / 去前视
│   ├─ cleaner.py            # 🧹 缺失 + 极值
│   └─ storage.py            # 💾 Parquet I/O
└─ scripts/
    ├─ build_data_warehouse.py
    └─ update_universe.py     # 自动更新股票池
```

## 安装和使用

### 1. 安装依赖

```bash
pip install tushare pandas pyarrow python-dotenv tqdm rich
```

### 2. 配置

创建一个`.env`文件（可从`.env.template`复制），填入你的Tushare API Token：

```
TUSHARE_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 3. 更新股票池

您可以使用`update_universe.py`脚本从Tushare自动获取并更新股票池：

```bash
# 默认使用沪深300成分股，市值100亿以上
python scripts/update_universe.py

# 也可以自定义参数
# 中证500成分股
python scripts/update_universe.py --index_code 000905.SH

# 科创板股票
python scripts/update_universe.py --market 科创板 --index_code None

# 市值1000亿以上的股票
python scripts/update_universe.py --index_code None --min_market_cap 1000
```

### 4. 运行数据获取脚本

```bash
python scripts/build_data_warehouse.py
```

## 数据流程

1. **获取数据**：从Tushare API获取日线和财务数据
2. **清洗数据**：去除停牌日，处理缺失值
3. **对齐数据**：将财务数据对齐到日线，确保无前视偏差
4. **标准化**：对因子进行去极值和标准化处理
5. **存储**：按年月分区存储为Parquet格式，带指纹检测避免重复写入

## 验证清单

| 检查项 | 快速方法 |
|-------|---------|
| 前视行数 = 0 | `df[df.index < df['pub_date']].shape[0]` |
| 缺失率 < 1% | `joined.isna().mean().mean()` |
| Parquet 读取速度 | `pd.read_parquet("data/processed/2025/07/*.parquet", columns=["close"])` < 2s |
| 重跑哈希不变 | 连续执行脚本应只输出 "✅ 数据仓刷新完成" 无新增写入日志 |

## 加速技巧

- 多线程并发：使用`concurrent.futures.ThreadPoolExecutor`加速数据获取
- 交易日索引缓存：全局复用交易日历以提高对齐效率
- 增量更新：只获取最新数据，与本地数据拼接以加快更新速度
