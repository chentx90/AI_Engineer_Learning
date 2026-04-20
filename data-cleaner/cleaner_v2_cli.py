import argparse

import pandas as pd
import os
import sys
from datetime import datetime


def load_data(file_path: str) -> pd.DataFrame:
    """安全加载CSV文件,

    Args:
        file_path （str): CSV文件的绝对或相对路径

    Returns：
        pd.DataFrame: 加载数据，若失败则退出程序
    """
    try:
        df = pd.read_csv(file_path)
        print(f"✅ 成功加载数据：{df.shape[0]} 行 × {df.shape[1]} 列")
        return df
    except FileNotFoundError:
        print(f"❌ 严重错误：找不到文件 '{file_path}'。请检查路径是否正确！")
        sys.exit(1)    # 找不到源文件，强行退出程序
    except pd.errors.EmptyDataError:
        print(f"❌ 严重错误：文件 '{file_path}'是空的！")
        sys.exit(1)


def clean_price_column(df):
    """清洗价格列，处理缺失值，移除货币符号，转换为浮点数"""
    original_missing = df['price'].isnull().sum()

    # 移除美元货币符号
    df['price'] = df['price'].astype(str).str.replace('$', '', regex=False)

    # 将空字符串和'nan',转换成真正的NaN
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    # 用列中位数填充缺失值
    median_price = df['price'].median()
    df['price'] = df['price'].fillna(median_price)

    new_missing = df['price'].isnull().sum()
    print(f"💰 价格列清洗：处理了{original_missing}个缺失值，用中位数{median_price:.2f}填充")

    return df

def parse_dates(df):
    """确保日期列格式为正确的datetime格式"""
    df['last_updated'] = pd.to_datetime(df['last_updated'], errors='coerce')
    print(f"📅 日期列已转换为标准格式") 
    return df

def generate_report(df, original_df):
    """生成清洁报告"""
    print("\n" + "="*50)
    print("📊 数据清洗报告")
    print("="*50)

    print("\n缺失值处理汇总:")
    for col in  original_df.columns:
        orig_missing = original_df[col].isnull().sum()
        new_missing = df[col].isnull().sum()
        if orig_missing > 0 or new_missing > 0:
            print(f" {col}:{orig_missing} -> {new_missing}个缺失值")

    # 数据质量指标
    print(f"\n数据完整性:{100 - (df.isnull().sum().sum() / df.size * 100):.1f}%")
    print(f"价格范围：${df['price'].min():.2f} - ${df['price'].max():.2f}")
    print(f"平均评分：{df['rating'].mean():.1f}/5.0")

    return df

def main():
    """主函数：执行完整清理流程"""


    # 1. 设置argparse
    parser = argparse.ArgumentParser(description="数据清洗器CLI工具 v0.2")

    # 设置input参数
    parser.add_argument(
        "-i", "--input",
        type = str,
        required = True,
        help = "输入的原始 CSV 文件路径"
    )
    parser.add_argument(
        "-o", "--output",
        type = str,
        default = "cleaned_result.csv",
        help="输出的 CSV 文件路径"
    )

    args = parser.parse_args()

    print(f"🛒 开始清洗数据...")
    print(f"📥 输入文件: {args.input}")
    print(f"📤 输出文件: {args.output}")
    print("-" * 40)

    original_df = load_data(args.input)
    df = original_df.copy()

    df = clean_price_column(df)
    df = parse_dates(df)

    # 保存清洗后的数据
    df.to_csv(args.output, index=False)
    print(f"\n💾 清洗后数据已保存至: {args.output}")

     # 生成报告
    generate_report(df, original_df)

    print("\n✨ 清洗完成！")
    
if __name__ == "__main__":
    main()