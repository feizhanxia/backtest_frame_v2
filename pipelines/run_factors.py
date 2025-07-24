#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子生成流程
从原始数据计算所有配置的因子并保存
"""

import sys
import pandas as pd
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.data_interface import DataInterface
from engine.factor_engine import FactorEngine


def main():
    """主流程：生成所有因子"""
    print("=" * 60)
    print("开始因子生成流程")
    print("=" * 60)
    
    try:
        # 1. 初始化引擎
        print("\n1. 初始化数据接口和因子引擎...")
        data_interface = DataInterface()
        factor_engine = FactorEngine()
        
        # 2. 加载基础数据
        print("\n2. 加载价格数据...")
        price_data = data_interface.get_price_data()
        
        # 检查价格数据状态
        if not price_data or all(df.empty for df in price_data.values()):
            print("❌ 价格数据为空")
            return False
        
        # 获取主要信息
        close_data = price_data.get('close', pd.DataFrame())
        if not close_data.empty:
            print(f"   价格数据形状: {close_data.shape}")
            print(f"   标的池大小: {len(close_data.columns)} 个标的")
        else:
            print("❌ 收盘价数据为空")
            return False
        
        # 3. 计算所有因子
        print("\n3. 计算所有配置的因子...")
        # ETF/指数只需要价格数据，不需要财务数据
        factors_df = factor_engine.compute_all_factors(price_data, {})
        
        if factors_df.empty:
            print("❌ 因子计算失败或无有效因子")
            return False
        
        print(f"   因子矩阵形状: {factors_df.shape}")
        print(f"   因子列表: {list(factors_df.columns.get_level_values(0).unique())}")
        
        # 4. 保存因子数据
        print("\n4. 保存因子数据...")
        data_interface.save_factor_data(factors_df, "all_factors")
        output_path = PROJECT_ROOT / "reports" / "factors" / "all_factors.parquet"
        print(f"   因子数据已保存至: {output_path}")
        
        # 5. 生成简单统计报告
        print("\n5. 生成因子统计报告...")
        generate_factor_report(factors_df)
        
        print("\n" + "=" * 60)
        print("✅ 因子生成流程完成")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 因子生成流程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_factor_report(factors_df: pd.DataFrame):
    """生成因子基础统计报告"""
    try:
        factor_names = factors_df.columns.get_level_values(0).unique()
        
        print(f"\n   因子数量: {len(factor_names)}")
        print("   各因子覆盖率统计:")
        
        for factor_name in factor_names:
            factor_data = factors_df[factor_name]
            total_values = factor_data.size
            valid_values = factor_data.dropna().size
            coverage = valid_values / total_values if total_values > 0 else 0
            
            print(f"     {factor_name}: {coverage:.2%} ({valid_values}/{total_values})")
        
        # 保存简单统计到文件
        report_path = PROJECT_ROOT / "reports" / "factor_summary.txt"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("因子生成统计报告\n")
            f.write("=" * 40 + "\n")
            f.write(f"生成时间: {pd.Timestamp.now()}\n")
            f.write(f"数据时间范围: {factors_df.index.min()} 至 {factors_df.index.max()}\n")
            f.write(f"因子数量: {len(factor_names)}\n")
            f.write(f"标的数量: {len(factors_df.columns.get_level_values(1).unique())}\n")
            f.write(f"总观测值: {factors_df.size}\n")
            f.write(f"有效观测值: {factors_df.dropna().size}\n\n")
            
            f.write("各因子覆盖率:\n")
            for factor_name in factor_names:
                factor_data = factors_df[factor_name]
                total_values = factor_data.size
                valid_values = factor_data.dropna().size
                coverage = valid_values / total_values if total_values > 0 else 0
                f.write(f"  {factor_name}: {coverage:.2%}\n")
        
        print(f"   统计报告已保存至: {report_path}")
        
    except Exception as e:
        print(f"   生成统计报告时出错: {e}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
