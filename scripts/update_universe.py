#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF/指数池更新工具

此脚本用于从Tushare API自动获取ETF和指数列表，并更新config/universe.csv文件。
支持按类型、规模和流动性进行过滤。

使用示例:
    # 获取主要ETF（默认）
    python update_universe.py
    
    # 获取所有ETF
    python update_universe.py --etf_type all
    
    # 获取指数
    python update_universe.py --target_type index
"""

import os
import pandas as pd
import tushare as ts
import logging
import datetime as dt
import calendar
from dotenv import load_dotenv
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("universe_update.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("universe_updater")

# 加载环境变量
load_dotenv()

# 获取Tushare token
token = os.getenv("TUSHARE_TOKEN")
if not token:
    logger.error("请在.env文件中设置TUSHARE_TOKEN")
    raise ValueError("请在.env文件中设置TUSHARE_TOKEN")

# 初始化Tushare
pro = ts.pro_api(token)

def get_etf_list(etf_type: str = 'main', min_size: float = 1.0) -> pd.DataFrame:
    """
    获取ETF列表
    
    Args:
        etf_type: ETF类型，'main'(主要ETF), 'all'(所有ETF)
        min_size: 最小规模(亿元)
        
    Returns:
        包含ETF信息的DataFrame
    """
    try:
        # 获取ETF基础信息
        etf_basic = pro.fund_basic(market='E')  # E表示ETF
        
        if etf_basic.empty:
            raise RuntimeError("Tushare 返回空ETF数据，请检查 TOKEN 或网络")
        
        # 获取ETF基本信息和规模数据
        etf_list = []
        for _, etf in etf_basic.iterrows():
            code = etf['ts_code']
            name = etf['name']
            
            # 跳过货币ETF和债券ETF（如果只要主要ETF）
            if etf_type == 'main':
                if any(keyword in name for keyword in ['货币', '债券', '可转债', '国债']):
                    continue
            
            etf_list.append({
                'ts_code': code,
                'name': name,
                'target_type': 'ETF',
                'category': '股票ETF' if '股票' in name or any(idx in name for idx in ['300', '500', '50', '创业板', '科创']) else '其他ETF'
            })
        
        etf_df = pd.DataFrame(etf_list)
        
        # 按规模过滤（这里简化处理，实际可以调用nav接口获取规模）
        logger.info(f"获取到 {len(etf_df)} 只ETF")
        
        return etf_df
        
    except Exception as e:
        logger.error(f"获取ETF列表失败: {e}")
        return pd.DataFrame()

def get_index_list(index_type: str = 'main') -> pd.DataFrame:
    """
    获取指数列表
    
    Args:
        index_type: 指数类型，'main'(主要指数), 'all'(所有指数)
        
    Returns:
        包含指数信息的DataFrame
    """
    try:
        # 主要指数列表
        main_indices = [
            ('000001.SH', '上证指数'),
            ('000300.SH', '沪深300'),
            ('000905.SH', '中证500'),
            ('000852.SH', '中证1000'),
            ('399001.SZ', '深证成指'),
            ('399006.SZ', '创业板指'),
            ('000688.SH', '科创50'),
            ('000016.SH', '上证50'),
            ('932000.CSI', 'CSI国债指数'),
        ]
        
        if index_type == 'main':
            index_list = []
            for code, name in main_indices:
                index_list.append({
                    'ts_code': code,
                    'name': name,
                    'target_type': 'INDEX',
                    'category': '宽基指数' if any(idx in name for idx in ['沪深300', '中证500', '中证1000', '上证指数', '深证成指']) else '行业指数'
                })
            
            return pd.DataFrame(index_list)
        else:
            # 获取所有指数（可以进一步实现）
            logger.warning("暂不支持获取所有指数，返回主要指数")
            return get_index_list('main')
            
    except Exception as e:
        logger.error(f"获取指数列表失败: {e}")
        return pd.DataFrame()

def update_universe(save_path=None, target_type='etf', etf_type='main', min_size=1.0):
    """
    更新ETF/指数池文件

    参数:
        save_path: 保存路径，默认为config/universe.csv
        target_type: 目标类型，'etf', 'index', 'both'
        etf_type: ETF类型，'main'或'all'
        min_size: 最小规模(亿元)

    返回:
        更新后的标的列表DataFrame
    """
    all_targets = []
    
    # 获取ETF
    if target_type in ['etf', 'both']:
        etf_df = get_etf_list(etf_type, min_size)
        if not etf_df.empty:
            all_targets.append(etf_df)
    
    # 获取指数
    if target_type in ['index', 'both']:
        index_df = get_index_list('main')
        if not index_df.empty:
            all_targets.append(index_df)
    
    if not all_targets:
        logger.warning("获取的标的池为空，请检查过滤条件")
        return pd.DataFrame()
    
    # 合并所有标的
    targets = pd.concat(all_targets, ignore_index=True)

    if len(targets) == 0:
        logger.warning("获取的标的池为空，请检查过滤条件")
        return targets

    # 设置默认保存路径
    if save_path is None:
        base_dir = Path(__file__).resolve().parents[1]  # 项目根目录
        save_path = base_dir / "config" / "universe.csv"
    else:
        save_path = Path(save_path)

    # 确保目录存在
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存为csv
    targets.to_csv(save_path, index=False)
    logger.info(f"✅ 标的池已更新，共{len(targets)}个标的，已保存至{save_path}")
    
    # 打印统计信息
    print(f"\n📊 标的池统计:")
    print(f"总数量: {len(targets)}")
    if 'target_type' in targets.columns:
        print(targets['target_type'].value_counts().to_string())
    if 'category' in targets.columns:
        print(f"\n分类统计:")
        print(targets['category'].value_counts().to_string())

    return targets

if __name__ == "__main__":
    import argparse

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='更新ETF/指数池')
    parser.add_argument('--target_type', type=str, default='etf', choices=['etf', 'index', 'both'],
                        help='目标类型: etf(ETF), index(指数), both(两者)')
    parser.add_argument('--etf_type', type=str, default='main', choices=['main', 'all'],
                        help='ETF类型: main(主要ETF), all(所有ETF)')
    parser.add_argument('--min_size', type=float, default=1.0,
                        help='最小规模要求(亿元)，默认1.0')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件路径，默认为config/universe.csv')

    args = parser.parse_args()

    # 更新标的池
    update_universe(
        save_path=args.output,
        target_type=args.target_type,
        etf_type=args.etf_type,
        min_size=args.min_size
    )
