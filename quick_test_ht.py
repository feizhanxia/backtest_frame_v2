#!/usr/bin/env python3
"""
快速测试 ht_trendmode 因子
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from engine.data_interface import DataInterface
from engine.factor_engine import FactorEngine

def quick_test():
    print("🧪 快速测试 ht_trendmode...")
    
    # 初始化
    data_interface = DataInterface()
    factor_engine = FactorEngine()
    
    # 获取少量数据进行快速测试
    print("📊 获取测试数据...")
    price_data = data_interface.get_price_data("20240601", "20250101")
    
    # 只取前10只股票进行测试
    test_symbols = list(price_data['close'].columns)[:10]
    test_close = price_data['close'][test_symbols]
    
    print(f"测试数据形状: {test_close.shape}")
    print(f"数据覆盖期间: {test_close.index[0]} 到 {test_close.index[-1]}")
    
    # 测试ht_trendmode
    print("\n🔍 测试 ht_trendmode 因子...")
    try:
        factor_matrix = factor_engine.compute_factor('ht_trendmode', {'close': test_close})
        
        if factor_matrix.empty:
            print("❌ ht_trendmode: 计算结果为空")
        else:
            print(f"✅ ht_trendmode: 计算成功!")
            print(f"   结果形状: {factor_matrix.shape}")
            valid_values = factor_matrix.count().sum()
            total_values = factor_matrix.size
            coverage = valid_values / total_values * 100
            print(f"   数据覆盖率: {coverage:.1f}% ({valid_values}/{total_values})")
            
            # 显示部分结果
            print(f"   前5行前5列结果:")
            print(factor_matrix.iloc[:5, :5])
            
    except Exception as e:
        print(f"❌ ht_trendmode: 错误 - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()
