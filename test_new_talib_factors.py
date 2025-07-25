#!/usr/bin/env python3
"""
测试新增的TA-Lib因子
验证重叠研究、动量、成交量和周期指标的实现
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from engine.data_interface import DataInterface
from engine.factor_engine import FactorEngine

def test_new_talib_factors():
    """测试新增的TA-Lib因子"""
    print("🧪 测试新增的TA-Lib因子...")
    
    # 初始化
    data_interface = DataInterface()
    factor_engine = FactorEngine()
    
    # 获取价格数据
    print("📊 获取价格数据...")
    price_data = data_interface.get_price_data("20240101", "20250101")
    
    print(f"数据概况: 形状 {price_data['close'].shape}")
    
    # 新增因子列表
    new_factors = {
        "重叠研究指标": [
            'dema20', 'wma20', 'trima20', 't3_20', 
            'midpoint14', 'midprice14', 'ht_trendline'
        ],
        "动量指标": [
            'adxr14', 'macdext_12_26_9', 'macdfix9',
            'minus_di14', 'minus_dm14', 'plus_di14', 'plus_dm14',
            'rocp10', 'rocr10', 'rocr100_10', 'stochrsi14'
        ],
        "成交量指标": ['obv_line'],
        "周期指标": [
            'ht_dcperiod', 'ht_dcphase', 'ht_phasor_inphase',
            'ht_phasor_quadrature', 'ht_sine', 'ht_leadsine', 'ht_trendmode'
        ]
    }
    
    # 测试结果统计
    total_factors = 0
    successful_factors = 0
    results = {}
    
    for category, factors in new_factors.items():
        print(f"\n🔍 测试 {category}:")
        category_results = []
        
        for factor_name in factors:
            try:
                factor_matrix = factor_engine.compute_factor(factor_name, price_data)
                
                if factor_matrix.empty:
                    print(f"  ❌ {factor_name}: 计算结果为空")
                    category_results.append((factor_name, False, 0))
                else:
                    # 计算覆盖率
                    coverage = (1 - factor_matrix.isna().sum().sum() / factor_matrix.size) * 100
                    print(f"  ✅ {factor_name}: 覆盖率 {coverage:.1f}%")
                    category_results.append((factor_name, True, coverage))
                    successful_factors += 1
                    
                total_factors += 1
                
            except Exception as e:
                print(f"  ❌ {factor_name}: 错误 - {e}")
                category_results.append((factor_name, False, 0))
                total_factors += 1
        
        results[category] = category_results
        success_rate = sum(1 for _, success, _ in category_results if success) / len(category_results) * 100
        print(f"    📈 {category} 成功率: {len([r for r in category_results if r[1]])}/{len(category_results)} ({success_rate:.1f}%)")
    
    # 总结
    print(f"\n🎯 总体测试结果:")
    print(f"  - 总因子数: {total_factors}")
    print(f"  - 成功因子数: {successful_factors}")
    print(f"  - 总成功率: {successful_factors}/{total_factors} ({successful_factors/total_factors*100:.1f}%)")
    
    # 显示高质量因子
    print(f"\n🏆 高质量因子 (覆盖率>70%):")
    high_quality = []
    for category, factors in results.items():
        for factor_name, success, coverage in factors:
            if success and coverage > 70:
                high_quality.append((factor_name, coverage))
    
    high_quality.sort(key=lambda x: x[1], reverse=True)
    for factor_name, coverage in high_quality[:10]:  # 显示前10个
        print(f"  📊 {factor_name}: {coverage:.1f}%")
    
    print(f"\n✅ 新TA-Lib因子测试完成! 共扩充了 {total_factors} 个专业技术分析指标")
    
    return results

if __name__ == "__main__":
    test_new_talib_factors()
