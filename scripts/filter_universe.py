#!/usr/bin/env python3
"""
过滤ETF/指数标的池
只保留有历史数据且适合分析的标的
"""

import pandas as pd
import tushare as ts
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
from tqdm import tqdm

load_dotenv()
pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def filter_universe():
    """过滤标的池，只保留有足够历史数据的标的"""
    
    # 读取完整标的池
    universe_file = Path(__file__).parent.parent / "config" / "universe.csv"
    df = pd.read_csv(universe_file)
    
    logger.info(f"原始标的池大小: {len(df)}")
    
    # 过滤条件
    valid_targets = []
    failed_targets = []
    
    # 分批处理，避免API限制
    batch_size = 50
    for i in tqdm(range(0, len(df), batch_size), desc="过滤标的池"):
        batch = df.iloc[i:i+batch_size]
        
        for idx, row in batch.iterrows():
            ts_code = row['ts_code']
            target_type = row['target_type']
            
            try:
                # 获取基础信息
                if target_type == 'ETF':
                    info = pro.fund_basic(ts_code=ts_code)
                    if info.empty:
                        failed_targets.append((ts_code, "无基础信息"))
                        continue
                        
                    list_date = info['list_date'].iloc[0]
                    delist_date = info['delist_date'].iloc[0]
                    
                    # 过滤条件
                    # 1. 上市时间早于2023年（确保有足够历史数据）
                    if pd.notna(list_date) and int(list_date) > 20230101:
                        failed_targets.append((ts_code, f"上市时间太晚: {list_date}"))
                        continue
                    
                    # 2. 未退市
                    if pd.notna(delist_date):
                        failed_targets.append((ts_code, f"已退市: {delist_date}"))
                        continue
                        
                else:
                    # 指数直接检查数据
                    pass
                
                # 尝试获取少量数据验证可用性
                if target_type == 'ETF':
                    test_data = pro.fund_daily(ts_code=ts_code, start_date='20220101', end_date='20220201')
                else:
                    test_data = pro.index_daily(ts_code=ts_code, start_date='20220101', end_date='20220201')
                
                if test_data is None or test_data.empty:
                    failed_targets.append((ts_code, "无历史数据"))
                    continue
                
                # 通过所有检查，加入有效列表
                valid_targets.append(row)
                
            except Exception as e:
                failed_targets.append((ts_code, f"检查出错: {str(e)}"))
                continue
        
        # 避免API限制，每批次后暂停
        if i < len(df) - batch_size:
            import time
            time.sleep(1)
    
    # 创建过滤后的标的池
    if valid_targets:
        filtered_df = pd.DataFrame(valid_targets)
        
        # 保存过滤后的标的池
        filtered_file = universe_file.parent / "universe_filtered.csv"
        filtered_df.to_csv(filtered_file, index=False)
        
        logger.info(f"过滤后标的池大小: {len(filtered_df)}")
        logger.info(f"过滤后标的池已保存至: {filtered_file}")
        
        # 保存失败记录
        if failed_targets:
            failed_df = pd.DataFrame(failed_targets, columns=['ts_code', 'reason'])
            failed_file = universe_file.parent / "universe_failed.csv"
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
    filter_universe()
