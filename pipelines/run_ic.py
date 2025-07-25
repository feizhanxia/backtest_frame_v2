#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IC分析流程
计算所有因子的IC时间序列和统计摘要
"""

import sys
import pandas as pd
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.data_interface import DataInterface
from engine.ic_engine import ICEngine


def main():
    """主流程：IC分析"""
    print("=" * 60)
    print("开始IC分析流程")
    print("=" * 60)
    
    try:
        # 1. 初始化引擎
        print("\n1. 初始化数据接口和IC引擎...")
        data_interface = DataInterface()
        ic_engine = ICEngine()
        
        # 2. 加载因子数据
        print("\n2. 加载因子数据...")
        factors_df = data_interface.load_factor_data("all_factors")
        
        if factors_df.empty:
            print("❌ 无法加载因子数据，请先运行 run_factors.py")
            return False
        
        print(f"   因子数据形状: {factors_df.shape}")
        factor_names = list(factors_df.columns.get_level_values(0).unique())
        print(f"   因子列表: {factor_names}")
        
        # 3. 获取前瞻收益率
        print("\n3. 计算前瞻收益率...")
        ret_df = data_interface.get_forward_returns()  # 现在会自动读取配置中的forward_return_days
        
        if ret_df.empty:
            print("❌ 无法计算前瞻收益率")
            return False
        
        print(f"   收益率数据形状: {ret_df.shape}")
        
        # 4. 计算多因子IC
        print("\n4. 计算所有因子的IC时间序列...")
        ic_df = ic_engine.calc_multi_factor_ic(factors_df, ret_df)
        
        if ic_df.empty:
            print("❌ IC计算失败")
            return False
        
        print(f"   IC矩阵形状: {ic_df.shape}")
        print(f"   IC时间范围: {ic_df.index.min()} 至 {ic_df.index.max()}")
        
        # 5. 生成IC分析报告
        print("\n5. 生成IC分析报告...")
        ic_report = ic_engine.generate_ic_report(ic_df)
        
        if not ic_report:
            print("❌ IC报告生成失败")
            return False
        
        # 6. 保存IC结果
        print("\n6. 保存IC分析结果...")
        ic_engine.save_ic_results(ic_report)
        
        # 7. 显示因子排名
        print("\n7. 因子表现排名:")
        display_factor_ranking(ic_report)
        
        print("\n" + "=" * 60)
        print("✅ IC分析流程完成")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ IC分析流程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def display_factor_ranking(ic_report: dict):
    """显示因子排名信息"""
    try:
        if 'factor_ranking' not in ic_report:
            print("   无因子排名数据")
            return
        
        ranking_df = ic_report['factor_ranking']
        
        if ranking_df.empty:
            print("   因子排名为空")
            return
        
        print(f"\n   前10名因子表现:")
        print("   " + "-" * 80)
        
        # 选择要显示的列
        display_cols = []
        if 'ic_ir_60d' in ranking_df.columns:
            display_cols.append('ic_ir_60d')
        if 'abs_ic_mean' in ranking_df.columns:
            display_cols.append('abs_ic_mean')
        if 'win_rate' in ranking_df.columns:
            display_cols.append('win_rate')
        if 'composite_score' in ranking_df.columns:
            display_cols.append('composite_score')
        
        # 显示前10名
        top_factors = ranking_df.head(10)
        
        for i, (factor_name, row) in enumerate(top_factors.iterrows(), 1):
            line = f"   {i:2d}. {factor_name:12s}"
            
            for col in display_cols:
                if col in row:
                    value = row[col]
                    if pd.notna(value):
                        if col == 'win_rate':
                            line += f" {col}:{value:6.1%}"
                        else:
                            line += f" {col}:{value:7.3f}"
                    else:
                        line += f" {col}:   N/A "
            
            print(line)
        
        # 保存排名到文件
        ranking_path = PROJECT_ROOT / "reports" / "factor_ranking.csv"
        ranking_df.to_csv(ranking_path, encoding='utf-8')
        print(f"\n   完整排名已保存至: {ranking_path}")
        
    except Exception as e:
        print(f"   显示因子排名时出错: {e}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
