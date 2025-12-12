import pandas as pd
import os

# =================配置区=================
# 这里填你 Excel 文件的完整路径
# 注意：引号前加 r，且路径两边有引号
SOURCE_FILE = r"E:\ZHX\Noon Intel\Noon_Master_Output_Full.xlsx"

# 输出文件会保存在同一个文件夹下
OUTPUT_FILE = r"E:\ZHX\Noon Intel\noon_data.parquet"
# ========================================

print(f"1. 正在读取大文件: {SOURCE_FILE}")
print("   (文件很大，请耐心等待 1-2 分钟，不要关闭窗口...)")

try:
    # 读取 Excel
    df = pd.read_excel(SOURCE_FILE)
    print(f"   ✅ 读取成功！包含 {len(df)} 行数据")

    print("2. 正在压缩转换为 Parquet 格式...")
    # 转换
    df.to_parquet(OUTPUT_FILE, index=False)
    
    # 获取文件大小对比
    size_excel = os.path.getsize(SOURCE_FILE) / (1024 * 1024)
    size_parquet = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)

    print(f"\n🎉 转换完成！")
    print(f"   原文件大小: {size_excel:.2f} MB")
    print(f"   新文件大小: {size_parquet:.2f} MB")
    print(f"   瘦身比例: {(1 - size_parquet/size_excel)*100:.1f}%")
    print(f"   文件已保存为: {OUTPUT_FILE}")

except FileNotFoundError:
    print("❌ 错误：找不到文件！请检查路径是否正确。")
except Exception as e:
    print(f"❌ 发生错误: {e}")