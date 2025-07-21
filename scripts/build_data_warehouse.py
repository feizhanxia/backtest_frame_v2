import pandas as pd, datetime as dt
from pathlib import Path
from tqdm import tqdm
import logging
import concurrent.futures
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import data_fetcher as F, aligner as A, cleaner as C, storage as S

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_build.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("data_warehouse")

# 配置参数
START = "20220101"
START_Q = "20210101"
BASE  = Path(__file__).resolve().parents[1]   # 项目根目录
THREADS = 5  # 并行线程数

def process_stock(code):
    """处理单只股票的数据获取和清洗流程
    
    Args:
        code: 股票代码
        
    Returns:
        成功处理返回True，否则返回False
    """
    try:
        # 获取日线数据
        price = F.fetch_daily(code, START, dt.date.today().strftime("%Y%m%d"))
        
        # 保存原始价格数据
        S.save_raw_data(price, BASE, code, "price")
        
        # 清洗价格数据
        price = C.clean_price(price)
        
        # 获取财务数据
        fin = F.fetch_financial(code, START_Q)
        
        # 保存原始财务数据
        S.save_raw_data(fin, BASE, code, "financial")
        
        # 对齐财务数据到日线
        fin_aligned = A.align_financial_to_daily(fin, price.index)
        
        # 合并数据并保存
        joined = price.join(fin_aligned, how="left")
        S.to_parquet_partition(joined, BASE, code)
        return True
    except Exception as e:
        logger.error(f"处理 {code} 时出错: {str(e)}")
        return False

def main():
    logger.info("开始构建数据仓库...")
    
    # 读取股票池
    try:
        codes = pd.read_csv(BASE/"config/universe.csv")["ts_code"].tolist()
        logger.info(f"股票池读取成功，共 {len(codes)} 只股票")
    except Exception as e:
        logger.error(f"读取股票池失败: {str(e)}")
        return
    
    # 并行处理各股票数据
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        # 提交所有任务
        futures = {executor.submit(process_stock, code): code for code in codes}
        
        # 处理结果
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(codes), ncols=80):
            code = futures[future]
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                logger.error(f"{code} 处理失败: {str(e)}")
    
    logger.info(f"✅ 数据仓刷新完成，成功处理 {success_count}/{len(codes)} 只股票")

if __name__ == "__main__":
    main()
