#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票池更新工具

此脚本用于从Tushare API自动获取股票列表，并更新config/universe.csv文件。
支持按指数成分股、市场类型和市值大小进行过滤。

使用示例:
    # 获取沪深300成分股（默认）
    python update_universe.py
    
    # 获取中证500成分股
    python update_universe.py --index_code 000905.SH
    
    # 获取科创板股票
    python update_universe.py --market 科创板 --index_code None
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

def get_stock_list(index_code: str | None = None,
                   market: str | None = None) -> pd.DataFrame:
    """
    获取股票列表，只做两件事：
    1) 从 Tushare 拉取全部在市股票；
    2) 可选：按 market 或 index_code 过滤。
    返回只含 ts_code 列的 DataFrame。
    """
    # ① 全市场股票
    stocks = pro.stock_basic(exchange='', list_status='L',
                             fields='ts_code,market')
    if stocks.empty:
        raise RuntimeError("Tushare 返回空数据，请检查 TOKEN 或网络")

    # ② 市场过滤（如 '主板'、'创业板'、'科创板'）
    if market:
        stocks = stocks[stocks['market'] == market]

    # ③ 指数成分过滤（如 '000300.SH'）
    if index_code:
        # 计算本月首日与末日
        today = dt.date.today()
        first_day = today.replace(day=1).strftime('%Y%m%d')
        last_day = today.replace(
            day=calendar.monthrange(today.year, today.month)[1]
        ).strftime('%Y%m%d')

        # 尝试本月区间
        index_df = pro.index_weight(
            index_code=index_code,
            start_date=first_day,
            end_date=last_day
        )

        # 若本月无数据，再回溯 2 个月（最多 3 次）
        back_months = 1
        while index_df.empty and back_months <= 2:
            ref = today - dt.timedelta(days=30 * back_months)
            first_day = ref.replace(day=1).strftime('%Y%m%d')
            last_day = ref.replace(
                day=calendar.monthrange(ref.year, ref.month)[1]
            ).strftime('%Y%m%d')
            index_df = pro.index_weight(
                index_code=index_code,
                start_date=first_day,
                end_date=last_day
            )
            back_months += 1

        if index_df.empty:
            raise RuntimeError(
                f"近 3 个月均未获取到 {index_code} 成分股数据，请检查指数代码或积分不足"
            )

        stocks = stocks[stocks['ts_code'].isin(index_df['con_code'])]

    return stocks[['ts_code']].reset_index(drop=True)

def update_universe(save_path=None, index_code=None, market=None):
    """
    更新股票池文件

    参数:
        save_path: 保存路径，默认为config/universe.csv
        index_code: 指数代码，如'000300.SH'为沪深300
        market: 市场类型

    返回:
        更新后的股票列表DataFrame
    """
    # 获取股票列表
    stocks = get_stock_list(index_code, market)

    if len(stocks) == 0:
        logger.warning("获取的股票池为空，请检查过滤条件")
        return stocks

    # 设置默认保存路径
    if save_path is None:
        base_dir = Path(__file__).resolve().parents[1]  # 项目根目录
        save_path = base_dir / "config" / "universe.csv"
    else:
        save_path = Path(save_path)

    # 确保目录存在
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存为csv
    stocks.to_csv(save_path, index=False)
    logger.info(f"✅ 股票池已更新，共{len(stocks)}只股票，已保存至{save_path}")

    return stocks

if __name__ == "__main__":
    import argparse

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='更新股票池')
    parser.add_argument('--index_code', type=str, default='000300.SH',
                        help='指数代码，如000300.SH为沪深300，000905.SH为中证500，设为None表示不使用指数过滤')
    parser.add_argument('--market', type=str, default=None,
                        help='市场类型，如"主板"、"创业板"、"科创板"等，默认为不过滤')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件路径，默认为config/universe.csv')

    args = parser.parse_args()

    # ---- 处理 "None" 字符串 ----
    if isinstance(args.index_code, str) and args.index_code.lower() == 'none':
        args.index_code = None

    if isinstance(args.market, str) and args.market.lower() == 'none':
        args.market = None

    # 更新股票池
    update_universe(
        save_path=args.output,
        index_code=args.index_code,
        market=args.market
    )
