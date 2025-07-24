import os, datetime as dt, warnings, tushare as ts, pandas as pd
from dotenv import load_dotenv; load_dotenv()

# 忽略来自pandas的FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")
# 忽略来自tushare的FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="tushare")

pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))

def fetch_daily(ts_code: str, start: str, end: str, asset_type: str = 'auto') -> pd.DataFrame:
    """获取日线数据（股票/ETF/指数，已前复权）
    
    Args:
        ts_code: 标的代码（如：000001.SZ, 510050.SH, 000300.SH）
        start: 起始日期，格式YYYYMMDD
        end: 结束日期，格式YYYYMMDD
        asset_type: 资产类型，'stock'(股票), 'fund'(ETF), 'index'(指数), 'auto'(自动识别)
        
    Returns:
        前复权后的日线数据，以trade_date为索引
    """
    try:
        # 自动识别资产类型
        if asset_type == 'auto':
            if ts_code.startswith(('510', '511', '512', '513', '515', '516', '518')):
                asset_type = 'fund'  # ETF
            elif ts_code.startswith(('000', '399')) and ('SH' in ts_code or 'SZ' in ts_code):
                # 指数（000300.SH, 399001.SZ等）
                asset_type = 'index'
            else:
                asset_type = 'stock'  # 默认为股票
        
        # 根据资产类型选择合适的接口
        if asset_type == 'fund':
            # ETF使用fund_daily接口
            df = pro.fund_daily(ts_code=ts_code, start_date=start, end_date=end)
            if df is None or df.empty:
                # 备选：使用pro_bar接口
                df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                               adj='qfq', freq='D', asset='FD')
        elif asset_type == 'index':
            # 指数使用index_daily接口
            df = pro.index_daily(ts_code=ts_code, start_date=start, end_date=end)
            if df is None or df.empty:
                # 备选：使用pro_bar接口
                df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                               freq='D', asset='I')
        else:
            # 股票使用原有逻辑
            df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                           adj='qfq', freq='D', asset='E')
        
        # 如果主要接口失败，尝试通用pro_bar接口
        if df is None or df.empty:
            print(f"警告：主接口获取 {ts_code} 的数据为空，尝试通用接口...")
            df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                           adj='qfq', freq='D')
        
        # 如果数据仍然为空，则记录错误
        if df is None or df.empty:
            raise ValueError(f"无法获取 {ts_code} 的日线数据")
            
        # 确保数据按日期排序
        df = df.sort_values("trade_date")
        
        # 检查必要的列是否存在
        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"获取的数据缺少必要的列：{missing_cols}")
        
        # 确保包含vol和amount列（某些指数可能没有）
        if 'vol' not in df.columns:
            df['vol'] = 0  # 指数没有成交量，设为0
        if 'amount' not in df.columns:
            df['amount'] = 0  # 指数没有成交额，设为0
        # 转换日期格式
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        
        # 提取需要的列并返回
        return df.set_index("trade_date")
    except Exception as e:
        print(f"获取 {ts_code} 的日线数据时出错: {str(e)}")
        # 创建一个空的DataFrame作为替代
        return pd.DataFrame(columns=["ts_code", "open", "high", "low", "close", "vol", "amount"])

# 删除财务数据获取函数，ETF/指数不需要财务数据
# def fetch_financial() 函数已移除
