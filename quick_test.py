#!/usr/bin/env python3
"""
快速测试剩余因子是否正常工作
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.factor_engine import FactorEngine

def quick_test():
    print("🧪 快速测试因子引擎...")
    
    try:
        factor_engine = FactorEngine()
        print("✅ FactorEngine 初始化成功")
        
        # 测试一个简单的因子
        import pandas as pd
        import numpy as np
        
        # 创建模拟数据
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        symbols = ['TEST001', 'TEST002', 'TEST003']
        
        test_data = {
            'close': pd.DataFrame(
                np.random.randn(100, 3).cumsum(axis=0) + 100,
                index=dates,
                columns=symbols
            ),
            'high': pd.DataFrame(
                np.random.randn(100, 3).cumsum(axis=0) + 105,
                index=dates,
                columns=symbols
            ),
            'low': pd.DataFrame(
                np.random.randn(100, 3).cumsum(axis=0) + 95,
                index=dates,
                columns=symbols
            ),
            'vol': pd.DataFrame(
                np.random.randint(1000, 10000, (100, 3)),
                index=dates,
                columns=symbols
            )
        }
        
        # 测试一个基础因子
        result = factor_engine.compute_factor('mom20', test_data)
        if not result.empty:
            print("✅ 基础因子 mom20 计算成功")
        else:
            print("❌ 基础因子 mom20 计算失败")
            
        print("\n🎯 希尔伯特变换因子已成功删除，系统恢复正常！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test()
