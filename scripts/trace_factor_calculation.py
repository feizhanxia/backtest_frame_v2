#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子计算过程诊断工具
追踪因子从原始数据到最终结果的完整流程
"""

import pandas as pd
import numpy as np
from engine.data_interface import DataInterface
from engine.factor_engine import FactorEngine
import yaml

def trace_factor_calculation():
    """追踪因子计算的完整过程"""
    
    print("🔍 追踪因子计算过程...")
    
    # 1. 初始化
    data_interface = DataInterface()
    factor_engine = FactorEngine()
    
    # 2. 获取原始价格数据
    print("\n=== 步骤1: 原始价格数据 ===")
    price_data = data_interface.get_price_data()
    
    close_data = price_data['close']
    print(f"原始close数据形状: {close_data.shape}")
    print(f"原始数据有效率: {close_data.notna().sum().sum() / (close_data.shape[0] * close_data.shape[1]) * 100:.2f}%")
    
    # 3. 逐步追踪mom20因子计算
    print("\n=== 步骤2: mom20因子原始计算 ===")
    
    # 直接计算20日动量（不经过standardize）
    raw_mom20 = close_data.pct_change(20, fill_method=None)
    print(f"原始mom20计算后形状: {raw_mom20.shape}")
    print(f"原始mom20有效率: {raw_mom20.notna().sum().sum() / (raw_mom20.shape[0] * raw_mom20.shape[1]) * 100:.2f}%")
    
    # 分析前20日数据（预期为NaN）
    first_20_days = raw_mom20.iloc[:20]
    print(f"前20日数据(预期NaN): {first_20_days.notna().sum().sum()} 个有效值")
    
    # 分析后续数据
    after_20_days = raw_mom20.iloc[20:]
    print(f"第21日起数据: {after_20_days.notna().sum().sum()} 个有效值")
    print(f"第21日起有效率: {after_20_days.notna().sum().sum() / (after_20_days.shape[0] * after_20_days.shape[1]) * 100:.2f}%")
    
    # 4. 追踪标准化处理的影响
    print("\n=== 步骤3: 标准化处理影响 ===")
    
    # forward_fill处理
    print("--- forward_fill处理 ---")
    after_ffill = factor_engine.forward_fill(raw_mom20, max_days=5)
    ffill_improvement = after_ffill.notna().sum().sum() - raw_mom20.notna().sum().sum()
    print(f"forward_fill后有效值增加: {ffill_improvement}")
    print(f"forward_fill后有效率: {after_ffill.notna().sum().sum() / (after_ffill.shape[0] * after_ffill.shape[1]) * 100:.2f}%")
    
    # winsorize处理
    print("--- winsorize处理 ---")
    after_winsorize = factor_engine.winsorize(after_ffill, quantiles=(0.01, 0.99))
    winsorize_change = after_winsorize.notna().sum().sum() - after_ffill.notna().sum().sum()
    print(f"winsorize后有效值变化: {winsorize_change}")
    print(f"winsorize后有效率: {after_winsorize.notna().sum().sum() / (after_winsorize.shape[0] * after_winsorize.shape[1]) * 100:.2f}%")
    
    # zscore处理
    print("--- zscore处理 ---")
    after_zscore = factor_engine.zscore(after_winsorize)
    zscore_change = after_zscore.notna().sum().sum() - after_winsorize.notna().sum().sum()
    print(f"zscore后有效值变化: {zscore_change}")
    print(f"zscore后有效率: {after_zscore.notna().sum().sum() / (after_zscore.shape[0] * after_zscore.shape[1]) * 100:.2f}%")
    
    # 5. 分析zscore的影响机制
    print("\n=== 步骤4: zscore影响机制分析 ===")
    
    # 逐日分析zscore处理
    daily_valid_before = []
    daily_valid_after = []
    
    for date in after_winsorize.index:
        before_count = after_winsorize.loc[date].notna().sum()
        after_count = after_zscore.loc[date].notna().sum()
        daily_valid_before.append(before_count)
        daily_valid_after.append(after_count)
    
    daily_valid_before = pd.Series(daily_valid_before, index=after_winsorize.index)
    daily_valid_after = pd.Series(daily_valid_after, index=after_zscore.index)
    
    # 找到损失最大的日期
    daily_loss = daily_valid_before - daily_valid_after
    worst_days = daily_loss.nlargest(10)
    
    print(f"每日平均有效标的数(zscore前): {daily_valid_before.mean():.1f}")
    print(f"每日平均有效标的数(zscore后): {daily_valid_after.mean():.1f}")
    print(f"每日平均损失标的数: {daily_loss.mean():.1f}")
    
    print(f"\n损失最严重的10个交易日:")
    for date, loss in worst_days.items():
        before = daily_valid_before[date]
        after = daily_valid_after[date]
        print(f"  {date.strftime('%Y-%m-%d')}: {before}→{after} (损失{loss})")
        
        # 分析这一天的具体情况
        day_data = after_winsorize.loc[date]
        if day_data.notna().sum() >= 2:  # 有足够数据计算std
            std_val = day_data.std()
            if std_val == 0:
                print(f"    原因: 标准差为0 (所有有效值相同)")
            else:
                print(f"    标准差: {std_val:.6f} (正常)")
        else:
            print(f"    原因: 有效样本数不足2个")
    
    # 6. 总结
    print(f"\n=== 总结 ===")
    total_possible = close_data.shape[0] * close_data.shape[1]
    final_valid = after_zscore.notna().sum().sum()
    
    print(f"数据流转过程:")
    print(f"  原始数据: {close_data.notna().sum().sum():,} / {total_possible:,} ({close_data.notna().sum().sum()/total_possible*100:.2f}%)")
    print(f"  mom20计算: {raw_mom20.notna().sum().sum():,} / {total_possible:,} ({raw_mom20.notna().sum().sum()/total_possible*100:.2f}%)")
    print(f"  forward_fill: {after_ffill.notna().sum().sum():,} / {total_possible:,} ({after_ffill.notna().sum().sum()/total_possible*100:.2f}%)")
    print(f"  winsorize: {after_winsorize.notna().sum().sum():,} / {total_possible:,} ({after_winsorize.notna().sum().sum()/total_possible*100:.2f}%)")
    print(f"  zscore: {final_valid:,} / {total_possible:,} ({final_valid/total_possible*100:.2f}%)")
    
    print(f"\n主要损失来源:")
    mom20_loss = close_data.notna().sum().sum() - raw_mom20.notna().sum().sum()
    zscore_loss = after_winsorize.notna().sum().sum() - final_valid
    print(f"  计算窗口期损失: {mom20_loss:,} ({mom20_loss/total_possible*100:.2f}%)")
    print(f"  zscore标准化损失: {zscore_loss:,} ({zscore_loss/total_possible*100:.2f}%)")

if __name__ == "__main__":
    trace_factor_calculation()
