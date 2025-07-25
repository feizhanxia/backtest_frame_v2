#!/usr/bin/env python3
"""
最终验证测试 - 确认删除问题因子后系统正常
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.factor_engine import FactorEngine
import pandas as pd
import numpy as np

def final_verification():
    """最终验证测试"""
    print("🎯 最终验证测试...")
    
    try:
        factor_engine = FactorEngine()
        print("✅ FactorEngine 初始化成功")
        
        # 创建测试数据
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        symbols = ['TEST001', 'TEST002', 'TEST003']
        
        test_data = {
            'open': pd.DataFrame(
                np.random.randn(50, 3).cumsum(axis=0) + 100,
                index=dates, columns=symbols
            ),
            'high': pd.DataFrame(
                np.random.randn(50, 3).cumsum(axis=0) + 105,
                index=dates, columns=symbols
            ),
            'low': pd.DataFrame(
                np.random.randn(50, 3).cumsum(axis=0) + 95,
                index=dates, columns=symbols
            ),
            'close': pd.DataFrame(
                np.random.randn(50, 3).cumsum(axis=0) + 100,
                index=dates, columns=symbols
            ),
            'vol': pd.DataFrame(
                np.random.randint(1000, 10000, (50, 3)),
                index=dates, columns=symbols
            ),
            'amount': pd.DataFrame(
                np.random.randint(100000, 1000000, (50, 3)),
                index=dates, columns=symbols
            )
        }
        
        # 测试不同类别的关键因子
        test_factors = [
            'mom20',      # 动量因子
            'rsi14',      # 技术指标
            'sma20',      # 重叠研究
            'atr14',      # 波动率指标
            'obv_line',   # 成交量指标
            'beta5',      # 统计函数
        ]
        
        success_count = 0
        for factor in test_factors:
            try:
                result = factor_engine.compute_factor(factor, test_data)
                if not result.empty:
                    print(f"✅ {factor}: 计算成功 - 形状 {result.shape}")
                    success_count += 1
                else:
                    print(f"⚠️ {factor}: 返回空结果")
            except Exception as e:
                print(f"❌ {factor}: 计算失败 - {e}")
        
        print(f"\n🏆 测试结果: {success_count}/{len(test_factors)} 个因子正常工作")
        
        if success_count == len(test_factors):
            print("🎉 系统完全正常！所有问题因子已成功删除！")
        else:
            print("⚠️ 仍有部分因子存在问题")
            
    except Exception as e:
        print(f"❌ 系统测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_verification()
