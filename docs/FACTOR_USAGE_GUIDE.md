# TA-Lib因子库使用指南

## 快速开始

### 1. 基本使用方法

```python
from engine.factor_engine import FactorEngine
import pandas as pd

# 初始化因子引擎
engine = FactorEngine()

# 加载数据
data = {
    'close': close_df,    # 收盘价DataFrame
    'high': high_df,      # 最高价DataFrame  
    'low': low_df,        # 最低价DataFrame
    'vol': volume_df      # 成交量DataFrame
}

# 计算单个因子
rsi_factor = engine.compute_factor('rsi14', data)

# 批量计算因子
factor_list = ['rsi14', 'sma20', 'ema20', 'macd_signal']
results = {}
for factor_name in factor_list:
    results[factor_name] = engine.compute_factor(factor_name, data)
```

### 2. 配置文件使用

```yaml
# config/factors.yml
factors:
  rsi14:
    enabled: true
    params:
      window: 14
    description: "14日RSI指标"
    category: "momentum"
```

## 因子分类详解

### 动量指标 (Momentum Indicators)
适用于捕捉价格趋势的强弱和转折点。

**推荐因子**:
- `rsi14` - RSI相对强弱指标 (最常用)
- `macd_signal` - MACD信号线
- `cci14` - CCI商品通道指标
- `bop` - 均衡成交量
- `williams_r` - 威廉指标

**使用示例**:
```python
# RSI超买超卖策略
rsi = engine.compute_factor('rsi14', data)
buy_signal = rsi < 30   # 超卖
sell_signal = rsi > 70  # 超买

# MACD趋势策略
macd = engine.compute_factor('macd_signal', data)
trend_up = macd > 0
trend_down = macd < 0
```

### 重叠研究指标 (Overlap Studies)  
用于趋势跟踪和支撑阻力位判断。

**推荐因子**:
- `sma20` - 20日简单移动平均
- `ema20` - 20日指数移动平均  
- `bbands_upper/lower` - 布林带上下轨
- `sar` - 抛物线SAR
- `mama_adaptive` - 自适应移动平均

**使用示例**:
```python
# 双均线策略
sma20 = engine.compute_factor('sma20', data)
sma50 = engine.compute_factor('sma50', data) 
golden_cross = sma20 > sma50  # 金叉

# 布林带策略
upper = engine.compute_factor('bbands_upper', data)
lower = engine.compute_factor('bbands_lower', data)
breakout_up = data['close'] > upper
support = data['close'] < lower
```

### 成交量指标 (Volume Indicators)
结合价格和成交量分析市场资金流向。

**推荐因子**:
- `obv_line` - 成交量平衡指标
- `ad_line` - 累积/派发线
- `adosc` - 累积/派发振荡器

**使用示例**:
```python
# OBV量价背离
obv = engine.compute_factor('obv_line', data)
price_up = data['close'].pct_change() > 0
obv_down = obv.pct_change() < 0
divergence = price_up & obv_down
```

### 波动率指标 (Volatility Indicators)
测量价格波动程度，用于风险管理。

**推荐因子**:
- `atr14` - 14日平均真实范围
- `natr14` - 标准化ATR
- `trange` - 真实范围

**使用示例**:
```python
# ATR止损策略
atr = engine.compute_factor('atr14', data)
stop_loss_long = data['close'] - 2 * atr
stop_loss_short = data['close'] + 2 * atr

# 波动率过滤器
high_vol = atr > atr.rolling(20).quantile(0.8)
low_vol = atr < atr.rolling(20).quantile(0.2)
```

### 统计函数 (Statistic Functions)
提供统计学角度的技术分析。

**推荐因子**:
- `beta5` - 5日贝塔系数
- `correl5` - 5日相关系数
- `linearreg14` - 14日线性回归
- `stddev20` - 20日标准差

### 数学变换 (Math Transform)
对价格数据进行数学变换处理。

**推荐因子**:
- `ln_transform` - 对数变换
- `sqrt_transform` - 平方根变换
- `max_value_30` - 30日最大值
- `min_value_30` - 30日最小值

## 高级使用技巧

### 1. 因子组合策略

```python
def create_composite_signal(data, engine):
    \"\"\"创建组合信号\"\"\"
    # 趋势因子
    sma20 = engine.compute_factor('sma20', data)
    ema12 = engine.compute_factor('ema12', data)
    
    # 动量因子  
    rsi = engine.compute_factor('rsi14', data)
    macd = engine.compute_factor('macd_signal', data)
    
    # 成交量因子
    obv = engine.compute_factor('obv_line', data)
    
    # 组合信号
    trend_signal = (data['close'] > sma20) & (ema12 > sma20)
    momentum_signal = (rsi > 50) & (macd > 0)
    volume_signal = obv > obv.shift(1)
    
    composite_signal = trend_signal & momentum_signal & volume_signal
    return composite_signal
```

### 2. 动态参数优化

```python
def optimize_rsi_params(data, engine, param_range=range(10, 25)):
    \"\"\"优化RSI参数\"\"\"
    best_param = 14
    best_score = 0
    
    for window in param_range:
        # 临时修改配置
        factor_config = engine.config['factors']['rsi14'].copy()
        factor_config['params']['window'] = window
        
        # 计算因子
        rsi = engine.compute_factor('rsi14', data, config=factor_config)
        
        # 计算策略收益(示例)
        signals = (rsi < 30) | (rsi > 70)
        score = calculate_strategy_return(signals, data['close'])
        
        if score > best_score:
            best_score = score
            best_param = window
    
    return best_param, best_score
```

### 3. 多时间框架分析

```python
def multi_timeframe_analysis(data, engine):
    \"\"\"多时间框架分析\"\"\"
    results = {}
    
    # 不同时间框架的移动平均
    timeframes = [5, 10, 20, 50, 200]
    
    for tf in timeframes:
        factor_name = f'sma{tf}'
        if factor_name in engine.config['factors']:
            results[f'sma_{tf}d'] = engine.compute_factor(factor_name, data)
    
    # 时间框架排列分析
    alignment = pd.DataFrame(index=data['close'].index, columns=data['close'].columns)
    
    for col in data['close'].columns:
        for i in range(len(timeframes)-1):
            shorter = results[f'sma_{timeframes[i]}d'][col]
            longer = results[f'sma_{timeframes[i+1]}d'][col]
            alignment[col] += (shorter > longer).astype(int)
    
    return alignment
```

## 性能优化建议

### 1. 数据预处理
```python
# 批量数据预处理
def preprocess_data(raw_data):
    \"\"\"批量预处理数据\"\"\"
    processed = {}
    for key, df in raw_data.items():
        # 填充缺失值
        processed[key] = df.ffill().bfill()
        # 数据类型优化
        processed[key] = processed[key].astype(np.float32)
    return processed
```

### 2. 并行计算
```python
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

def parallel_factor_computation(factor_list, data, engine):
    \"\"\"并行计算多个因子\"\"\"
    def compute_single_factor(factor_name):
        return factor_name, engine.compute_factor(factor_name, data)
    
    # 使用线程池
    max_workers = min(len(factor_list), multiprocessing.cpu_count())
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = dict(executor.map(compute_single_factor, factor_list))
    
    return results
```

### 3. 缓存机制
```python
import pickle
import hashlib

class FactorCache:
    \"\"\"因子计算缓存\"\"\"
    
    def __init__(self, cache_dir='cache/factors'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, factor_name, data_hash, params):
        \"\"\"生成缓存键\"\"\"
        key_str = f"{factor_name}_{data_hash}_{str(params)}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get_cached_factor(self, cache_key):
        \"\"\"获取缓存因子\"\"\"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def cache_factor(self, cache_key, factor_data):
        \"\"\"缓存因子数据\"\"\"
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump(factor_data, f)
```

## 注意事项

### 1. 数据质量要求
- 确保OHLC数据的一致性和完整性
- 处理股票分红除权等公司行为
- 注意数据的前复权/后复权处理

### 2. 参数设置
- 不同市场和品种需要调整参数
- 避免过度优化和曲线拟合
- 考虑参数的经济学意义

### 3. 性能考虑  
- 大数据量时考虑分批处理
- 使用合适的数据类型(float32 vs float64)
- 定期清理中间计算结果

### 4. 风险管理
- 单一因子信号强度有限
- 组合多个因子提高稳定性
- 实盘前充分回测验证

## 常见问题解答

**Q: 某些因子返回全NaN值怎么办？**
A: 检查数据长度是否足够，某些因子(如T3)需要大量历史数据。

**Q: 如何选择合适的参数？**  
A: 结合历史回测和滚动验证选择参数，避免过度拟合。

**Q: 因子计算速度太慢怎么优化？**
A: 使用并行计算、数据类型优化、缓存机制等方法。

**Q: 如何评估因子的有效性？**
A: 计算IC值、信息比率、夏普比率等指标评估因子质量。

通过本指南，您应该能够熟练使用TA-Lib因子库进行量化策略开发。如有更多问题，请参考技术文档或联系开发团队。
