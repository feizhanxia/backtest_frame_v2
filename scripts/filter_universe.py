#!/usr/bin/env python3
"""
过滤ETF/指数标的池
从universe.csv中筛选有历史数据且适合分析的标的，支持各种过滤条件
"""

import pandas as pd
import tushare as ts
import os
import argparse
from dotenv import load_dotenv
from pathlib import Path
import logging
from tqdm import tqdm

load_dotenv()
pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def filter_universe(target_type='both', etf_type='main', index_type='main', 
                    output_file='universe_small.csv'):
    """
    过滤标的池，基于名称和类型进行简单过滤（无需API调用）
    
    Args:
        target_type: 目标类型，'etf', 'index', 'both'
        etf_type: ETF类型，'main'(主要ETF), 'all'(所有ETF)
        index_type: 指数类型，'main'(主要指数), 'all'(所有指数)
        output_file: 输出文件名
    """
    
    # 读取完整标的池
    universe_file = Path(__file__).parent.parent / "config" / "universe.csv"
    if not universe_file.exists():
        logger.error(f"标的池文件不存在: {universe_file}")
        return
    
    df = pd.read_csv(universe_file)
    logger.info(f"原始标的池大小: {len(df)}")
    
    # 过滤目标类型
    if target_type == 'etf':
        df = df[df['target_type'] == 'ETF']
    elif target_type == 'index':
        df = df[df['target_type'] == '指数']
    # 'both' 保留所有
    
    logger.info(f"按类型过滤后: {len(df)}")
    
    # 简化过滤条件，只基于名称和代码进行过滤
    valid_targets = []
    failed_targets = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="过滤标的池"):
        ts_code = row['ts_code']
        row_target_type = row['target_type']
        name = row['name']
        
        try:
            # 根据类型进行不同的检查
            if row_target_type == 'ETF':
                # ETF过滤逻辑
                if etf_type == 'main':
                    # 跳过货币ETF和债券ETF
                    if any(keyword in name for keyword in ['货币', '债券', '可转债', '国债', '短债', '中债', '长债']):
                        failed_targets.append((ts_code, "过滤掉货币/债券ETF"))
                        continue
                    
                    # 跳过一些特殊类型的ETF
                    if any(keyword in name for keyword in ['REITs', 'QDII', '商品', '黄金', '原油', '白银']):
                        failed_targets.append((ts_code, "过滤掉特殊类型ETF"))
                        continue
            
            else:
                # 指数过滤逻辑
                if index_type == 'main':
                    # 只保留主要指数
                    main_indices = ['000001.SH', '000300.SH', '000905.SH', '000852.SH', 
                                    '399001.SZ', '399006.SZ', '000688.SH', '000016.SH', '932000.CSI']
                    if ts_code not in main_indices:
                        failed_targets.append((ts_code, "非主要指数"))
                        continue
            
            # 通过所有检查，加入有效列表
            valid_targets.append(row)
            
        except Exception as e:
            failed_targets.append((ts_code, f"检查出错: {str(e)}"))
            continue
    
    # 创建过滤后的标的池
    if valid_targets:
        filtered_df = pd.DataFrame(valid_targets)
        
        # 保存过滤后的标的池
        output_path = Path(__file__).parent.parent / "config" / output_file
        filtered_df.to_csv(output_path, index=False)
        
        logger.info(f"过滤后标的池大小: {len(filtered_df)}")
        logger.info(f"过滤后标的池已保存至: {output_path}")
        
        # 保存失败记录
        if failed_targets:
            failed_df = pd.DataFrame(failed_targets, columns=['ts_code', 'reason'])
            failed_file = output_path.parent / f"{output_file.replace('.csv', '_failed.csv')}"
            failed_df.to_csv(failed_file, index=False)
            logger.info(f"失败标的记录已保存至: {failed_file}")
        
        # 显示分类统计
        print("\n=== 过滤结果统计 ===")
        print(f"原始标的数量: {len(df)}")
        print(f"有效标的数量: {len(filtered_df)}")
        print(f"失败标的数量: {len(failed_targets)}")
        
        if len(filtered_df) > 0:
            print(f"\n有效标的类型分布:")
            print(filtered_df['target_type'].value_counts())
            
        print(f"\n失败原因统计:")
        failed_df = pd.DataFrame(failed_targets, columns=['ts_code', 'reason'])
        print(failed_df['reason'].value_counts())
        
    else:
        logger.error("没有找到任何有效标的！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='过滤ETF/指数标的池（简化版，无API调用）')
    parser.add_argument('--target_type', type=str, default='both', choices=['etf', 'index', 'both'],
                        help='目标类型: etf(ETF), index(指数), both(两者)')
    parser.add_argument('--etf_type', type=str, default='main', choices=['main', 'all'],
                        help='ETF类型: main(主要ETF), all(所有ETF)')
    parser.add_argument('--index_type', type=str, default='main', choices=['main', 'all'],
                        help='指数类型: main(主要指数), all(所有指数)')
    parser.add_argument('--output', type=str, default='universe_small.csv',
                        help='输出文件名，默认universe_small.csv')

    args = parser.parse_args()

    filter_universe(
        target_type=args.target_type,
        etf_type=args.etf_type,
        index_type=args.index_type,
        output_file=args.output
    )
