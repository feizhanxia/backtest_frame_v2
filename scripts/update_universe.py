#!/usr/bin/env python3
"""
ETF/指数池更新工具
获取所有ETF和指数，保存到config/universe.csv
"""

import os
import pandas as pd
import tushare as ts
import logging
import time
from dotenv import load_dotenv
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量并初始化Tushare
load_dotenv()
pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))

def get_all_etfs():
    """获取所有ETF"""
    try:
        etf_basic = pro.fund_basic(market='E')
        time.sleep(1.2)  # API频率控制：每分钟不超过50次
        if etf_basic.empty:
            return pd.DataFrame()
        
        etf_list = []
        for _, etf in etf_basic.iterrows():
            etf_list.append({
                'ts_code': etf['ts_code'],
                'name': etf['name'],
                'target_type': 'ETF',
                'category': 'ETF'
            })
        
        logger.info(f"获取到 {len(etf_list)} 只ETF")
        return pd.DataFrame(etf_list)
        
    except Exception as e:
        logger.error(f"获取ETF列表失败: {e}")
        return pd.DataFrame()

def get_all_indices():
    """获取所有指数（包括SSE、SZSE、CSI、CNI）"""
    all_indices = []
    
    # 上交所指数
    try:
        sse_indices = pro.index_basic(market='SSE')
        time.sleep(1.2)  # API频率控制：每分钟不超过50次
        if not sse_indices.empty:
            for _, idx in sse_indices.iterrows():
                all_indices.append({
                    'ts_code': idx['ts_code'],
                    'name': idx['name'],
                    'target_type': '指数',
                    'category': '指数'
                })
            logger.info(f"获取上交所指数 {len(sse_indices)} 个")
    except Exception as e:
        logger.warning(f"获取上交所指数失败: {e}")
    
    # 深交所指数
    try:
        szse_indices = pro.index_basic(market='SZSE')
        time.sleep(1.2)  # API频率控制：每分钟不超过50次
        if not szse_indices.empty:
            for _, idx in szse_indices.iterrows():
                all_indices.append({
                    'ts_code': idx['ts_code'],
                    'name': idx['name'],
                    'target_type': '指数',
                    'category': '指数'
                })
            logger.info(f"获取深交所指数 {len(szse_indices)} 个")
    except Exception as e:
        logger.warning(f"获取深交所指数失败: {e}")
    
    # 中证指数
    try:
        csi_indices = pro.index_basic(market='CSI')
        time.sleep(1.2)  # API频率控制：每分钟不超过50次
        if not csi_indices.empty:
            for _, idx in csi_indices.iterrows():
                all_indices.append({
                    'ts_code': idx['ts_code'],
                    'name': idx['name'],
                    'target_type': '指数',
                    'category': '指数'
                })
            logger.info(f"获取中证指数 {len(csi_indices)} 个")
    except Exception as e:
        logger.warning(f"获取中证指数失败: {e}")
    
    # 国证指数
    try:
        cni_indices = pro.index_basic(market='CNI')
        time.sleep(1.2)  # API频率控制：每分钟不超过50次
        if not cni_indices.empty:
            for _, idx in cni_indices.iterrows():
                all_indices.append({
                    'ts_code': idx['ts_code'],
                    'name': idx['name'],
                    'target_type': '指数',
                    'category': '指数'
                })
            logger.info(f"获取国证指数 {len(cni_indices)} 个")
    except Exception as e:
        logger.warning(f"获取国证指数失败: {e}")
    
    if all_indices:
        df = pd.DataFrame(all_indices)
        df = df.drop_duplicates(subset=['ts_code'])  # 去重
        logger.info(f"获取全部指数 {len(df)} 个（去重后）")
        return df
    else:
        return pd.DataFrame()

def update_universe():
    """更新ETF/指数池，获取所有ETF和指数保存到config/universe.csv"""
    
    # 获取所有ETF
    etf_df = get_all_etfs()
    
    # 获取所有指数
    index_df = get_all_indices()
    
    # 合并数据
    all_targets = []
    if not etf_df.empty:
        all_targets.append(etf_df)
    if not index_df.empty:
        all_targets.append(index_df)
    
    if not all_targets:
        logger.error("无法获取任何数据")
        return
    
    # 合并所有标的
    targets = pd.concat(all_targets, ignore_index=True)
    
    # 保存到config/universe.csv
    base_dir = Path(__file__).resolve().parents[1]
    save_path = base_dir / "config" / "universe.csv"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    targets.to_csv(save_path, index=False)
    
    logger.info(f"✅ 标的池已更新，共{len(targets)}个标的，已保存至{save_path}")
    print(f"\n📊 标的池统计:")
    print(f"总数量: {len(targets)}")
    print(targets['target_type'].value_counts().to_string())

if __name__ == "__main__":
    update_universe()
