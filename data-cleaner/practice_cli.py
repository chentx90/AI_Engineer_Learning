import argparse

def main():
    # 创建解析器对象（description 会在 --help 时提示）
    parser = argparse.ArgumentParser(description="这是一个打招呼工具！")

    # 添加对象
    # --name是名字参数，required=Ture表示这是必填，help这是参数说明
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="请输入你要打招呼的名字"
    )
     # --times是可选参数
    parser.add_argument(
        "--times",
        type=int,
        default=1,
        help="打招呼的次数"
    )
    # 解析参数
    args = parser.parse_args()

    # 使用参数
    for _ in range(args.times):
        print(f"Hello, AI Engineer {args.name}!")

if __name__ == "__main__":
    main()
