import pandas as pd
import plotly.express as px

# 日志文件名
log_file = "cpu_usage_bitz.log"
# 图表输出文件名
chart_file = "cpu_usage_chart.html"

try:
    # 读取 CSV 文件，跳过第一行标题，指定列名
    # 使用 parse_dates 将 'Timestamp' 列解析为日期时间对象
    df = pd.read_csv(log_file, skiprows=1, names=['Timestamp', 'CPU%'], parse_dates=['Timestamp'])

    # 检查数据是否为空
    if df.empty:
        print(f"错误：日志文件 '{log_file}' 为空或无法正确解析。")
        exit()

    # --- Plotly plotting starts ---
    # 使用 plotly.express 创建交互式线图
    fig = px.line(df, x='Timestamp', y='CPU%', title=f'BITZ Process CPU Usage Over Time ({log_file})', markers=True)

    # 更新布局以改善外观 (可选，plotly 默认通常不错)
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='CPU Usage (%)',
        hovermode="x unified" # 悬停时显示同一时间点的所有数据
    )
    # Plotly 通常会自动处理日期格式，无需手动设置 formatter/locator

    # --- Plotly plotting ends ---

    # 保存图表到 HTML 文件
    fig.write_html(chart_file)
    print(f"交互式图表已保存为 '{chart_file}'")

except FileNotFoundError:
    print(f"错误：找不到日志文件 '{log_file}'。请确保它在当前目录。")
except Exception as e:
    print(f"处理日志或生成图表时发生错误：{e}")
