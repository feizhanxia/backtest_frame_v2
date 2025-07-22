#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
因子融合流程
基于IC分析结果进行多因子融合
"""

import sys
import pandas as pd
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.data_interface import DataInterface
from engine.fusion_engine import FusionEngine


def main():
    """主流程：因子融合"""
    print("=" * 60)
    print("开始因子融合流程")
    print("=" * 60)
    
    try:
        # 1. 初始化引擎
        print("\n1. 初始化数据接口和融合引擎...")
        data_interface = DataInterface()
        fusion_engine = FusionEngine()
        
        # 2. 加载因子数据
        print("\n2. 加载因子数据...")
        factors_df = data_interface.load_factor_data("all_factors")
        
        if factors_df.empty:
            print("❌ 无法加载因子数据，请先运行 run_factors.py")
            return False
        
        print(f"   因子数据形状: {factors_df.shape}")
        factor_names = list(factors_df.columns.get_level_values(0).unique())
        print(f"   因子列表: {factor_names}")
        
        # 3. 加载IC分析结果
        print("\n3. 加载IC分析结果...")
        ic_summary = load_ic_summary()
        
        if ic_summary.empty:
            print("⚠️  无IC分析结果，将只执行等权融合")
            print("   建议先运行 run_ic.py 生成IC分析")
        else:
            print(f"   IC摘要数据形状: {ic_summary.shape}")
        
        # 4. 获取前瞻收益率（用于LightGBM融合）
        print("\n4. 加载前瞻收益率数据...")
        ret_df = data_interface.get_forward_returns()
        
        if ret_df.empty:
            print("⚠️  无前瞻收益率数据，将跳过LightGBM融合")
        else:
            print(f"   收益率数据形状: {ret_df.shape}")
        
        # 5. 执行多种融合方法
        print("\n5. 执行因子融合...")
        
        # 确定可用的融合方法
        available_methods = ['equal_weight']
        if not ic_summary.empty:
            available_methods.append('ic_weight')
        if not ret_df.empty:
            available_methods.append('lgb')
        
        print(f"   可用融合方法: {available_methods}")
        
        # 执行融合
        fusion_results = fusion_engine.fuse_factors(
            factors_df=factors_df,
            ic_summary=ic_summary if not ic_summary.empty else None,
            ret_df=ret_df if not ret_df.empty else None,
            methods=available_methods
        )
        
        if not fusion_results:
            print("❌ 融合失败，无有效结果")
            return False
        
        # 6. 保存融合结果
        print("\n6. 保存融合结果...")
        fusion_engine.save_fusion_results(fusion_results)
        
        # 7. 生成融合报告
        print("\n7. 生成融合统计报告...")
        generate_fusion_report(fusion_results)
        
        print("\n" + "=" * 60)
        print("✅ 因子融合流程完成")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 因子融合流程出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def load_ic_summary():
    """加载IC分析摘要"""
    try:
        ic_summary_path = PROJECT_ROOT / "reports" / "ic_summary.csv"
        if ic_summary_path.exists():
            return pd.read_csv(ic_summary_path, index_col=0, encoding='utf-8')
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"   加载IC摘要时出错: {e}")
        return pd.DataFrame()


def generate_fusion_report(fusion_results: dict):
    """生成融合统计报告"""
    try:
        report_path = PROJECT_ROOT / "reports" / "fusion_summary.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("因子融合统计报告\n")
            f.write("=" * 40 + "\n")
            f.write(f"生成时间: {pd.Timestamp.now()}\n")
            f.write(f"融合方法数量: {len(fusion_results)}\n\n")
            
            for method, result_df in fusion_results.items():
                f.write(f"融合方法: {method}\n")
                f.write("-" * 20 + "\n")
                
                if result_df.empty:
                    f.write("  结果为空\n\n")
                    continue
                
                f.write(f"  数据形状: {result_df.shape}\n")
                f.write(f"  时间范围: {result_df.index.min()} 至 {result_df.index.max()}\n")
                f.write(f"  股票数量: {len(result_df.columns)}\n")
                f.write(f"  有效观测: {result_df.dropna().size} / {result_df.size}\n")
                
                # 基础统计
                fusion_values = result_df.stack().dropna()
                if len(fusion_values) > 0:
                    f.write(f"  均值: {fusion_values.mean():.6f}\n")
                    f.write(f"  标准差: {fusion_values.std():.6f}\n")
                    f.write(f"  最小值: {fusion_values.min():.6f}\n")
                    f.write(f"  最大值: {fusion_values.max():.6f}\n")
                
                f.write("\n")
        
        print(f"   融合报告已保存至: {report_path}")
        
        # 显示简要统计
        print("\n   融合结果简要统计:")
        for method, result_df in fusion_results.items():
            if not result_df.empty:
                coverage = result_df.dropna().size / result_df.size
                print(f"     {method}: 形状{result_df.shape}, 覆盖率{coverage:.1%}")
            else:
                print(f"     {method}: 空结果")
        
    except Exception as e:
        print(f"   生成融合报告时出错: {e}")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
