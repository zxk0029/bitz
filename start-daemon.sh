#!/bin/bash

# 获取当前脚本所在目录的绝对路径，也就是项目根目录
PROJECT_PATH=$(cd "$(dirname "$0")" && pwd)
PLIST_TEMPLATE="com.bitz.collector.plist"
TEMP_PLIST_DIR="/tmp/bitz_launchd" # 临时文件目录
TEMP_PLIST_FILE="$TEMP_PLIST_DIR/com.bitz.collector.plist.tmp"
PLIST_PATH_FILE=".daemon.plistpath" # 存储临时 plist 路径的文件
EXECUTABLE_PATH="$PROJECT_PATH/target/release/bitz" # 定义可执行文件路径

echo "正在构建项目 (release模式)..."
# 进入项目目录执行 cargo build
(cd "$PROJECT_PATH" && cargo build --release)

# 检查构建是否成功
if [ $? -ne 0 ]; then
    echo "错误: 项目构建失败！请检查错误信息。"
    exit 1
fi
echo "项目构建成功: $EXECUTABLE_PATH"


# 检查模板文件是否存在
if [ ! -f "$PLIST_TEMPLATE" ]; then
    echo "错误: 模板文件 $PLIST_TEMPLATE 未找到！"
    exit 1
fi

# 创建临时目录
mkdir -p "$TEMP_PLIST_DIR"

echo "当前项目路径: $PROJECT_PATH"
echo "生成临时的 plist 文件: $TEMP_PLIST_FILE"

# 使用 sed 替换占位符并写入临时文件
# 使用 # 作为 sed 分隔符，避免路径中的 / 引起冲突
# 同时，确保模板中的路径与 EXECUTABLE_PATH 匹配
sed "s#__PROJECT_PATH__#$PROJECT_PATH#g" "$PLIST_TEMPLATE" > "$TEMP_PLIST_FILE"

# 检查替换是否成功
if [ $? -ne 0 ]; then
    echo "错误: 生成临时 plist 文件失败！"
    exit 1
fi

# 确保旧的服务已卸载（如果存在）
if [ -f "$PLIST_PATH_FILE" ]; then
    OLD_TEMP_PLIST=$(cat "$PLIST_PATH_FILE")
    # 检查服务是否仍在运行，基于 Label
    if launchctl list | grep -q com.bitz.collector; then
         # 检查正在运行的服务是否是由记录的临时文件加载的
         RUNNING_PLIST_PATH=$(launchctl dumpstate | grep "$OLD_TEMP_PLIST" -B 1 | head -n 1 | awk '{print $NF}')
         if [[ "$RUNNING_PLIST_PATH" == *"$OLD_TEMP_PLIST"* ]]; then
             echo "卸载旧的服务实例 ($OLD_TEMP_PLIST)..."
             launchctl unload "$OLD_TEMP_PLIST" >/dev/null 2>&1
         else
             echo "警告: 检测到名为 com.bitz.collector 的服务，但似乎不是由 $OLD_TEMP_PLIST 加载的。跳过卸载。"
         fi
    fi
fi

echo "加载并启动 BITZ Collector 服务..."
# 加载新的临时 plist 文件
launchctl load "$TEMP_PLIST_FILE"

# 检查加载是否成功
if [ $? -ne 0 ]; then
    echo "错误: 加载 launchd 服务失败！请检查 $TEMP_PLIST_FILE 内容是否正确，以及 $EXECUTABLE_PATH 是否存在且可执行。"
    exit 1
fi

# 保存临时 plist 的路径，供 stop 脚本使用
echo "$TEMP_PLIST_FILE" > "$PLIST_PATH_FILE"

echo "服务已加载。使用 'launchctl list | grep com.bitz.collector' 检查状态。"
echo "日志文件位于: $PROJECT_PATH/bitz_collector_out.log 和 $PROJECT_PATH/bitz_collector_err.log"
echo "使用 './stop-daemon.sh' 来停止和卸载服务。"