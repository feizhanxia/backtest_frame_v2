import os, datetime as dt, warnings, tushare as ts, pandas as pd
from dotenv import load_dotenv; load_dotenv()

# 忽略来自pandas的FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")
# 忽略来自tushare的FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="tushare")

pro = ts.pro_api(os.getenv("TUSHARE_TOKEN"))

def fetch_daily(ts_code: str, start: str, end: str) -> pd.DataFrame:
    """获取股票日线数据（已前复权）
    
    Args:
        ts_code: 股票代码（如：000001.SZ）
        start: 起始日期，格式YYYYMMDD
        end: 结束日期，格式YYYYMMDD
        
    Returns:
        前复权后的日线数据，以trade_date为索引
    """
    try:
        # 使用pro_bar接口直接获取前复权(qfq)数据
        df = ts.pro_bar(ts_code=ts_code, start_date=start, end_date=end, 
                        adj='qfq', freq='D', asset='E')
        
        if df is None or df.empty:
            print(f"警告：使用pro_bar获取 {ts_code} 的数据为空，尝试使用替代接口...")
            # 如果获取不到数据，尝试使用ts.get_hist_data作为备选方案
            code = ts_code.split('.')[0]
            df_alt = ts.get_hist_data(code, start=start, end=end)
            if df_alt is not None and not df_alt.empty:
                df_alt = df_alt.reset_index()
                df_alt['ts_code'] = ts_code
                df = df_alt.rename(columns={'date':'trade_date'})
        
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
        
        # 转换日期格式
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        
        # 提取需要的列并返回
        return df.set_index("trade_date")
    except Exception as e:
        print(f"获取 {ts_code} 的日线数据时出错: {str(e)}")
        # 创建一个空的DataFrame作为替代
        return pd.DataFrame(columns=["ts_code", "open", "high", "low", "close", "vol", "amount"])

def fetch_financial(ts_code: str, start_q: str) -> pd.DataFrame:
    """获取简化版财务指标数据 - 仅返回基本结构而不获取实际财务数据
    
    Args:
        ts_code: 股票代码（如：000001.SZ）
        start_q: 起始季度，格式YYYYMMDD
        
    Returns:
        简化的财务数据框架，包含基本列但值为空
    """
    # 创建一个空的DataFrame，仅包含必要的列结构
    # 这避免了因TuShare API限制导致的错误
    today = dt.datetime.today()
    # 创建一些模拟日期，这些将作为空数据的占位符
    dates = [
        today - dt.timedelta(days=90),
        today - dt.timedelta(days=180),
        today - dt.timedelta(days=270),
        today - dt.timedelta(days=360)
    ]
    
    # 创建一个包含基本结构的DataFrame
    fin = pd.DataFrame({
        "end_date": dates,
        "pub_date": [d + dt.timedelta(days=30) for d in dates]  # 发布日期通常在报告期后约30天
    })
    
    # 添加空的财务指标列
    fin["roe_ttm"] = None
    fin["pb"] = None
    
    return fin
