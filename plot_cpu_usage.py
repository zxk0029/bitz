import pandas as pd
import plotly.graph_objects as go
import http.server
import socketserver
import sys

# 日志文件名
log_file = "cpu_usage_bitz.log"
# 图表输出文件名
chart_file = "cpu_usage_chart.html"
# 移动平均窗口大小
window_size = 10
# 本地服务器端口
PORT = 8000

try:
    # 读取 CSV 文件，跳过第一行标题，指定列名
    # 使用 parse_dates 将 'Timestamp' 列解析为日期时间对象
    df = pd.read_csv(log_file, skiprows=1, names=['Timestamp', 'CPU%'], parse_dates=['Timestamp'])

    # 检查数据是否为空
    if df.empty:
        print(f"错误：日志文件 '{log_file}' 为空或无法正确解析。")
        exit()

    # --- 计算移动平均 --- 
    # center=True 使窗口中心对齐当前点, min_periods=1 处理边缘数据
    df['CPU%_smoothed'] = df['CPU%'].rolling(window=window_size, center=True, min_periods=1).mean()

    # --- Plotly plotting starts ---
    # 使用 graph_objects 创建图表以绘制多条线
    fig = go.Figure()

    # 添加原始数据线 (半透明)
    fig.add_trace(go.Scatter(
        x=df['Timestamp'], 
        y=df['CPU%'], 
        mode='lines+markers', 
        name='Original CPU%', 
        marker=dict(size=3),
        line=dict(width=1),
        opacity=0.6
    ))

    # 添加平滑后的数据线
    fig.add_trace(go.Scatter(
        x=df['Timestamp'], 
        y=df['CPU%_smoothed'], 
        mode='lines', 
        name=f'Smoothed CPU% (Window={window_size})',
        line=dict(width=2) # 加粗一点
    ))

    # 更新布局以改善外观
    fig.update_layout(
        title=f'BITZ Process CPU Usage Over Time ({log_file})',
        xaxis_title='Time',
        yaxis_title='CPU Usage (%)',
        hovermode="x unified", # 悬停时显示同一时间点的所有数据
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01) # 图例位置
    )

    # --- Plotly plotting ends ---

    # 保存图表到 HTML 文件
    fig.write_html(chart_file)
    print(f"交互式图表已保存为 '{chart_file}'")

    # --- 启动本地 HTTP 服务器 --- 
    Handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"\n将在本地启动 HTTP 服务器...")
            print(f"请在浏览器中打开: http://localhost:{PORT}/{chart_file}")
            print(f"按 Ctrl+C 停止服务器并退出脚本。")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 48: # Address already in use
             print(f"\n错误: 端口 {PORT} 已被占用。无法启动服务器。")
             print(f"请手动在浏览器中打开文件: {chart_file}")
        else:
             print(f"\n启动服务器时发生错误: {e}")
    except KeyboardInterrupt:
        print("\n服务器已停止。")
        sys.exit(0)

except FileNotFoundError:
    print(f"错误：找不到日志文件 '{log_file}'。请确保它在当前目录。")
except Exception as e:
    print(f"处理日志或生成图表时发生错误：{e}")
