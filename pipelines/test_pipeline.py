# -*- coding: utf-8 -*-
"""
量化因子框架完整测试
验证端到端的因子计算、IC分析、因子融合流程
"""
import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from engine.data_interface import DataInterface
from engine.factor_engine import FactorEngine
from engine.ic_engine import ICEngine
from engine.fusion_engine import FusionEngine

def main():
    """量化因子框架完整测试"""
    print("🚀 量化因子框架完整测试")
    print("="*60)
    
    start_time = time.time()
    
    try:
        # 1. 初始化各引擎
        print("\n📌 步骤 1/6: 初始化引擎...")
        data_interface = DataInterface()
        factor_engine = FactorEngine()
        ic_engine = ICEngine()
        fusion_engine = FusionEngine()
        print("✅ 引擎初始化完成")
        
        # 2. 计算因子
        print("\n📌 步骤 2/6: 计算因子...")
        price_data = data_interface.get_price_data()
        fin_data = {}  # ETF/指数不需要财务数据
        
        # 获取启用的因子
        enabled_factors = [name for name, config in factor_engine.config['factors'].items() 
                          if config.get('enabled', False)]
        
        print(f"启用的因子: {enabled_factors}")
        
        # 计算因子
        factor_results = {}
        for factor_name in enabled_factors:
            print(f"   计算因子: {factor_name}")
            factor_df = factor_engine.compute_factor(factor_name, price_data, fin_data)
            if not factor_df.empty:
                factor_results[factor_name] = factor_df
                print(f"   ✅ {factor_name}: {factor_df.shape}")
            else:
                print(f"   ❌ {factor_name}: 计算失败")
        
        print(f"✅ 成功计算 {len(factor_results)} 个因子")
        
        # 3. 计算IC分析
        print("\n📌 步骤 3/6: IC分析...")
        forward_returns = data_interface.get_forward_returns(days=1)
        
        if forward_returns.empty:
            print("❌ 前瞻收益计算失败")
            return False
        
        # 计算各因子IC
        ic_results = {}
        for factor_name, factor_df in factor_results.items():
            ic_series = ic_engine.calc_ic_timeseries(factor_df, forward_returns)
            if not ic_series.empty:
                ic_results[factor_name] = ic_series
                ic_mean = ic_series.mean()
                ic_ir = ic_mean / ic_series.std() if ic_series.std() > 0 else 0
                print(f"   {factor_name}: IC={ic_mean:.4f}, IR={ic_ir:.4f}")
        
        ic_df = pd.DataFrame(ic_results)
        ic_report = ic_engine.generate_ic_report(ic_df)
        print(f"✅ IC分析完成，矩阵形状: {ic_df.shape}")
        
        # 4. 因子融合
        print("\n📌 步骤 4/6: 因子融合...")
        
        # 创建因子矩阵
        factor_dfs = []
        for factor_name, factor_df in factor_results.items():
            factor_df_copy = factor_df.copy()
            factor_df_copy.columns = pd.MultiIndex.from_product([[factor_name], factor_df.columns])
            factor_dfs.append(factor_df_copy)
        
        factor_matrix = pd.concat(factor_dfs, axis=1)
        print(f"因子矩阵形状: {factor_matrix.shape}")
        
        # 等权融合
        equal_weights = fusion_engine.equal_weight_fusion(list(factor_results.keys()))
        equal_factor = fusion_engine.apply_weights(factor_matrix, equal_weights)
        
        # IC加权融合
        ic_weights = fusion_engine.ic_weight_fusion(ic_df)
        ic_factor = fusion_engine.apply_weights(factor_matrix, ic_weights)
        
        print(f"✅ 融合完成 - 等权: {equal_factor.shape}, IC加权: {ic_factor.shape}")
        
        # 5. 融合因子表现验证
        print("\n📌 步骤 5/6: 融合因子验证...")
        
        equal_ic = ic_engine.calc_ic_timeseries(equal_factor, forward_returns)
        ic_weighted_ic = ic_engine.calc_ic_timeseries(ic_factor, forward_returns)
        
        equal_summary = ic_engine.calc_ic_summary(equal_ic)
        ic_weighted_summary = ic_engine.calc_ic_summary(ic_weighted_ic)
        
        print(f"   等权融合: IC={equal_summary.get('ic_mean_full', 0):.4f}, "
              f"IR={equal_summary.get('ic_ir_full', 0):.4f}")
        print(f"   IC加权融合: IC={ic_weighted_summary.get('ic_mean_full', 0):.4f}, "
              f"IR={ic_weighted_summary.get('ic_ir_full', 0):.4f}")
        print("✅ 融合因子验证完成")
        # 6. 保存所有结果
        # 6. 保存结果
        print("\n📌 步骤 6/6: 保存结果...")
        
        # 确保输出目录存在
        output_dir = Path("reports/factors")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存IC报告
        ic_engine.save_ic_results(ic_report)
        
        # 保存因子数据
        for factor_name, factor_df in factor_results.items():
            factor_df.to_csv(output_dir / f"{factor_name}.csv")
        
        # 保存融合因子
        equal_factor.to_csv(output_dir / "fusion_equal_weight.csv")
        ic_factor.to_csv(output_dir / "fusion_ic_weight.csv")
        
        # 保存权重
        weights_df = pd.DataFrame([equal_weights, ic_weights], 
                                 index=['equal_weight', 'ic_weight'])
        weights_df.to_csv(Path("reports") / "fusion_weights.csv")
        
        print("✅ 所有结果已保存")
        
        # 7. 测试总结
        end_time = time.time()
        elapsed = end_time - start_time
        
        print("\n" + "="*60)
        print("🎉 量化因子框架测试成功！")
        print(f"⏱️  总耗时: {elapsed:.1f} 秒")
        print("="*60)
        
        print("\n📊 单因子表现排名:")
        if 'factor_ranking' in ic_report and not ic_report['factor_ranking'].empty:
            ranking = ic_report['factor_ranking']
            print(ranking[['ic_mean_full', 'ic_ir_full', 'win_rate', 'rank']].round(4))
        
        print("\n🔗 融合因子表现:")
        print(f"等权融合:   IC={equal_summary.get('ic_mean_full', 0):.4f}, IR={equal_summary.get('ic_ir_full', 0):.4f}")
        print(f"IC加权融合: IC={ic_weighted_summary.get('ic_mean_full', 0):.4f}, IR={ic_weighted_summary.get('ic_ir_full', 0):.4f}")
        
        print("\n📈 权重分配:")
        print("等权:", {k: f"{v:.3f}" for k, v in equal_weights.items()})
        print("IC权重:", {k: f"{v:.3f}" for k, v in ic_weights.items()})
        
        print("\n🎯 框架测试完成，可以开始后续的回测开发！")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
