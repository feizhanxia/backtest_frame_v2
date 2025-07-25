#!/usr/bin/env python3
"""
数据对齐分析脚本
分析不同指数的历史数据长度和时间对齐情况
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from engine.data_interface import DataInterface
import pandas as pd

def analyze_data_alignment():
    """分析数据对齐情况"""
    print("🔍 数据对齐分析")
    print("="*60)
    
    # 初始化数据接口
    data_interface = DataInterface()
    
    print(f"📋 Universe配置: {len(data_interface.universe)}个标的")
    print(f"📅 配置的时间范围: {data_interface.config['data']['start_date']} - {data_interface.config['data']['end_date']}")
    
    # 获取价格数据（使用当前的对齐逻辑）
    print("\n🔄 加载价格数据...")
    price_data = data_interface.get_price_data()
    
    if price_data['close'].empty:
        print("❌ 没有加载到任何数据")
        return
    
    close_data = price_data['close']
    print(f"📊 当前数据形状: {close_data.shape}")
    print(f"📅 实际时间范围: {close_data.index.min().date()} - {close_data.index.max().date()}")
    
    # 分析每个标的的数据覆盖情况
    print("\n📈 各标的数据覆盖分析:")
    print("-" * 80)
    print(f"{'标的代码':<15} {'数据量':<8} {'起始日期':<12} {'结束日期':<12} {'覆盖率':<8}")
    print("-" * 80)
    
    total_days = len(close_data.index)
    coverage_stats = []
    
    for col in close_data.columns:
        valid_data = close_data[col].dropna()
        if len(valid_data) > 0:
            start_date = valid_data.index.min().date()
            end_date = valid_data.index.max().date()
            coverage = len(valid_data) / total_days
            coverage_stats.append({
                'code': col,
                'count': len(valid_data),
                'start': start_date,
                'end': end_date,
                'coverage': coverage
            })
            print(f"{col:<15} {len(valid_data):<8} {start_date} {end_date} {coverage:.1%}")
    
    # 统计分析
    if coverage_stats:
        coverage_values = [s['coverage'] for s in coverage_stats]
        print(f"\n📊 覆盖率统计:")
        print(f"   平均覆盖率: {sum(coverage_values)/len(coverage_values):.1%}")
        print(f"   最低覆盖率: {min(coverage_values):.1%}")
        print(f"   最高覆盖率: {max(coverage_values):.1%}")
        
        # 找出覆盖率较低的标的
        low_coverage = [s for s in coverage_stats if s['coverage'] < 0.5]
        if low_coverage:
            print(f"\n⚠️  覆盖率低于50%的标的 ({len(low_coverage)}个):")
            for s in sorted(low_coverage, key=lambda x: x['coverage']):
                print(f"   {s['code']}: {s['coverage']:.1%} ({s['count']}天, {s['start']}起)")
    
    # 分析缺失数据模式
    print(f"\n🕳️  缺失数据分析:")
    missing_by_date = close_data.isna().sum(axis=1)
    non_zero_missing = missing_by_date[missing_by_date > 0]
    
    if len(non_zero_missing) > 0:
        print(f"   有缺失数据的日期: {len(non_zero_missing)}天")
        print(f"   平均每日缺失: {non_zero_missing.mean():.1f}个标的")
        print(f"   最多缺失: {non_zero_missing.max()}个标的")
        
        # 显示缺失最多的几个日期
        top_missing = non_zero_missing.nlargest(5)
        print(f"   缺失最多的日期:")
        for date, count in top_missing.items():
            print(f"     {date.date()}: {count}个标的缺失")
    else:
        print("   ✅ 所有日期都没有缺失数据")

if __name__ == "__main__":
    analyze_data_alignment()
