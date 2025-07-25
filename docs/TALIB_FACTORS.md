# Talib 技术指标因子库使用说明

## 📊 **新增 Talib 因子列表**

基于强大的 TA-Lib 技术分析库，我们为系统新增了 8 个专业的技术指标因子：

### **1. RSI - 相对强弱指标 (`rsi14`)**
- **描述**: 衡量价格变动的速度和变化幅度，判断超买超卖状态
- **参数**: `window: 14` (计算周期)
- **应用**: 趋势反转信号识别
- **覆盖率**: ~5%

```yaml
rsi14:
  enabled: true
  window: 14
  description: "RSI相对强弱指标 (14日)"
```

### **2. MACD 柱状图 (`macd_histogram`)**
- **描述**: MACD 柱状图，表示 MACD 线与信号线的差值
- **参数**: `fast: 12, slow: 26, signal: 9`
- **应用**: 趋势变化的早期信号
- **覆盖率**: ~3%

```yaml
macd_histogram:
  enabled: true
  fast: 12
  slow: 26
  signal: 9
  description: "MACD柱状图因子"
```

### **3. 布林带位置 (`bollinger_position`)**
- **描述**: 价格在布林带中的相对位置 (0-1之间)
- **参数**: `window: 20, std_dev: 2.0`
- **应用**: 均值回归策略，超买超卖判断
- **覆盖率**: ~5%

```yaml
bollinger_position:
  enabled: true
  window: 20
  std_dev: 2.0
  description: "布林带位置因子"
```

### **4. 威廉指标 (`williams_r`)**
- **描述**: Williams %R 超买超卖指标
- **参数**: `window: 14`
- **应用**: 短期反转信号
- **覆盖率**: ~79%

```yaml
williams_r:
  enabled: true
  window: 14
  description: "威廉指标 Williams %R"
```

### **5. 随机指标 K 值 (`stoch_k`)**
- **描述**: KD 指标中的 K 值，衡量收盘价在最近 N 日高低价区间的位置
- **参数**: `k_period: 14, d_period: 3, smooth_k: 3`
- **应用**: 超买超卖及趋势判断
- **覆盖率**: ~5%

```yaml
stoch_k:
  enabled: true
  k_period: 14
  d_period: 3
  smooth_k: 3
  description: "随机指标 KD 中的 K 值"
```

### **6. 商品通道指标 (`cci14`)**
- **描述**: CCI 指标，衡量价格偏离统计平均值的程度
- **参数**: `window: 14`
- **应用**: 识别循环性转折点
- **覆盖率**: ~78%

```yaml
cci14:
  enabled: true
  window: 14
  description: "商品通道指标 CCI (14日)"
```

### **7. 平均趋向指标 (`adx14`)**
- **描述**: ADX 指标，衡量趋势强度
- **参数**: `window: 14`
- **应用**: 判断趋势的强弱
- **覆盖率**: ~4%

```yaml
adx14:
  enabled: true
  window: 14
  description: "平均趋向指标 ADX (14日)"
```

### **8. 能量潮指标 (`obv_signal`)**
- **描述**: OBV 指标的标准化信号版本
- **参数**: `window: 20` (标准化窗口)
- **应用**: 成交量价格关系分析
- **覆盖率**: ~79%

```yaml
obv_signal:
  enabled: true
  window: 20
  description: "能量潮指标 OBV 标准化信号"
```

## 🎯 **因子特性分析**

### **高覆盖率因子** (适合主要策略)
- `williams_r`: 79.29%
- `obv_signal`: 79.01%
- `cci14`: 78.35%

### **中等覆盖率因子** (补充多样性)
- `rsi14`: 5.12%
- `stoch_k`: 5.01%
- `bollinger_position`: 4.53%

### **特殊用途因子**
- `macd_histogram`: 2.62% (趋势转折早期信号)
- `adx14`: 3.88% (趋势强度判断)

## 🚀 **使用建议**

### **1. 策略组合建议**
```yaml
# 推荐的高效因子组合
factors:
  # 高覆盖率基础因子
  williams_r:
    enabled: true
  cci14:
    enabled: true
  obv_signal:
    enabled: true
    
  # 特色技术指标
  rsi14:
    enabled: true
  bollinger_position:
    enabled: true
```

### **2. 参数调优空间**
大部分 Talib 因子都支持参数调优：

```yaml
# RSI 参数优化示例
rsi14:
  enabled: true
  window: 21        # 尝试不同周期: 7, 14, 21, 28
  
# 布林带参数优化示例  
bollinger_position:
  enabled: true
  window: 20        # 窗口: 10, 20, 30
  std_dev: 2.5      # 标准差倍数: 1.5, 2.0, 2.5
```

### **3. 数据要求**
- **最低数据量**: 各因子需要不同的最小观测数
  - RSI/STOCH: 至少 20+ 个交易日
  - ADX: 至少 35+ 个交易日 (算法复杂)
  - MACD: 至少 35+ 个交易日
- **数据质量**: 需要 OHLCV 完整数据
- **ETF/指数适用**: 所有因子都适用于 ETF 和指数数据

## 📈 **性能监控**

使用以下命令监控新因子性能：

```bash
# 计算所有因子
python pipelines/run_factors.py

# IC 分析
python pipelines/run_ic.py

# 因子融合
python pipelines/run_fusion.py
```

## 🔧 **扩展指南**

如需添加更多 Talib 因子，请参考现有实现：

1. 在 `engine/factor_engine.py` 中添加计算函数
2. 在 `compute_factor` 方法中添加调用逻辑
3. 在 `config/factors.yml` 中添加配置
4. 运行测试验证

---
**🎉 现在您拥有了 14 个强大的技术指标因子，可以构建更加丰富和有效的量化策略！**
