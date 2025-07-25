#!/usr/bin/env python3
"""
本地universe生成脚本
从ETF0725.xlsx文件的"标的"sheet中读取"跟踪指数代码"列，生成universe_local.csv文件
"""

import pandas as pd
import os
import sys

def main():
    # 设置文件路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # 输入文件路径
    etf_file = os.path.join(project_root, 'data', 'ETF0725.xlsx')
    
    # 输出文件路径
    output_file = os.path.join(project_root, 'config', 'universe_local.csv')
    
    print(f"读取文件: {etf_file}")
    
    try:
        # 读取Excel文件的"标的"sheet
        df = pd.read_excel(etf_file, sheet_name='标的')
        
        print(f"成功读取Excel文件，共有 {len(df)} 行数据")
        print("列名:", df.columns.tolist())
        
        # 检查是否存在"跟踪指数代码"列
        if '跟踪指数代码' not in df.columns:
            print("错误: 未找到'跟踪指数代码'列")
            print("可用的列名:", df.columns.tolist())
            return False
        
        # 提取跟踪指数代码列
        tracking_codes = df['跟踪指数代码'].dropna().unique()
        
        print(f"找到 {len(tracking_codes)} 个唯一的跟踪指数代码")
        
        # 创建DataFrame并保存为CSV
        universe_df = pd.DataFrame(tracking_codes, columns=['code'])
        universe_df.to_csv(output_file, index=False, encoding='utf-8')
        
        print(f"成功生成universe文件: {output_file}")
        print("前10个代码:")
        print(universe_df.head(10))
        
        return True
        
    except FileNotFoundError:
        print(f"错误: 文件 {etf_file} 不存在")
        return False
    except Exception as e:
        print(f"处理文件时发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
