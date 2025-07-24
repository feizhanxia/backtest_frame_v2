#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主运行脚本 - 一键完成完整的因子计算到融合流程
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入各个流程脚本
import pipelines.run_factors as run_factors
import pipelines.run_ic as run_ic
import pipelines.run_fusion as run_fusion
import pipelines.test_pipeline as test_pipeline


def main():
    """主流程：完整的因子分析流程"""
    print("🚀 量化因子回测系统 v2.0")
    print("=" * 80)
    print("完整流程：因子计算 → IC分析 → 因子融合")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 步骤1：因子计算
        print("\n🔄 步骤 1/3: 因子计算")
        if not run_factors.main():
            print("❌ 因子计算失败，流程终止")
            return False
        
        # 步骤2：IC分析
        print("\n🔄 步骤 2/3: IC分析")
        if not run_ic.main():
            print("❌ IC分析失败，流程终止")
            return False
        
        # 步骤3：因子融合
        print("\n🔄 步骤 3/3: 因子融合")
        if not run_fusion.main():
            print("❌ 因子融合失败，流程终止")
            return False
        
        # 完成总结
        end_time = time.time()
        elapsed = end_time - start_time
        
        print("\n" + "=" * 80)
        print("🎉 完整流程执行成功！")
        print(f"⏱️  总耗时: {elapsed:.1f} 秒")
        print("=" * 80)
        
        # 显示输出文件位置
        print("\n📁 输出文件位置:")
        reports_dir = PROJECT_ROOT / "reports"
        
        output_files = [
            "factors/all_factors.parquet",
            "ic_timeseries.csv", 
            "ic_summary.csv",
            "factor_ranking.csv",
            "fusion_equal_weight.csv",
            "fusion_ic_weight.csv",
            "fusion_lgb.csv",
            "factor_summary.txt",
            "fusion_summary.txt"
        ]
        
        for file_path in output_files:
            full_path = reports_dir / file_path
            if full_path.exists():
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} (未生成)")
        
        print("\n🔧 下一步建议:")
        print("   1. 查看 reports/factor_ranking.csv 了解因子表现")
        print("   2. 使用 reports/fusion_*.csv 进行后续回测")
        print("   3. 根据IC分析结果调整因子参数")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        return False
    except Exception as e:
        print(f"\n❌ 主流程执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_single_step(step: str):
    """运行单个步骤"""
    print(f"🔄 执行单步骤: {step}")
    
    if step == "factors":
        return run_factors.main()
    elif step == "ic":
        return run_ic.main()
    elif step == "fusion":
        return run_fusion.main()
    elif step == "test":
        return test_pipeline.main()
    else:
        print(f"❌ 未知步骤: {step}")
        print("可用步骤: factors, ic, fusion, test")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 运行单个步骤
        step = sys.argv[1].lower()
        success = run_single_step(step)
    else:
        # 运行完整流程
        success = main()
    
    sys.exit(0 if success else 1)
