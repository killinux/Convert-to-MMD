#!/usr/bin/env python3
"""
XPS to PMX Plugin Sync Script
Syncs code from E: drive to Blender addons directory and updates timestamp
"""

import os
import shutil
import re
from datetime import datetime
import sys

# Define paths
SOURCE = r"E:\mywork\Convert-to-MMD\xps_to_pmx"
TARGET = r"C:\Users\haoni\AppData\Roaming\Blender Foundation\Blender\3.6\scripts\addons\xps_to_pmx"
INIT_FILE = os.path.join(TARGET, "__init__.py")

def print_header(title):
    """Print a formatted header"""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print()

def sync_files():
    """Sync files from source to target"""
    print("📁 检查源文件夹...")
    if not os.path.exists(SOURCE):
        print(f"✗ 错误：源文件夹不存在")
        print(f"  位置：{SOURCE}")
        return False

    print("✓ 找到源文件夹")
    print(f"  源: {SOURCE}")
    print()

    # Clear cache
    pycache = os.path.join(TARGET, "__pycache__")
    if os.path.exists(pycache):
        print("🧹 清除 Python 缓存...")
        shutil.rmtree(pycache, ignore_errors=True)
        print("✓ 缓存已清除")
        print()

    # Remove old target
    if os.path.exists(TARGET):
        print("🗑 删除旧插件文件夹...")
        shutil.rmtree(TARGET, ignore_errors=True)
        print("✓ 旧文件夹已删除")
        print()

    # Copy files
    print("📋 正在复制文件...")
    try:
        shutil.copytree(SOURCE, TARGET)
        print("✓ 文件复制成功")
        print()
        return True
    except Exception as e:
        print(f"✗ 文件复制失败：{e}")
        print()
        return False

def update_timestamp():
    """Update the last_updated timestamp in __init__.py"""
    print("⏰ 更新版本时间戳...")

    if not os.path.exists(INIT_FILE):
        print(f"✗ 错误：{INIT_FILE} 不存在")
        return None

    # Get current timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Read file
    try:
        with open(INIT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"✗ 读取文件失败：{e}")
        return None

    # Replace timestamp using regex
    new_content = re.sub(
        r'"last_updated":\s*"[^"]*"',
        f'"last_updated": "{now}"',
        content
    )

    # Write back
    try:
        with open(INIT_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✓ 时间戳已更新: {now}")
        print()
        return now
    except Exception as e:
        print(f"✗ 写入文件失败：{e}")
        return None

def verify_sync():
    """Verify the sync was successful"""
    print("✔ 验证同步结果...")

    if not os.path.exists(INIT_FILE):
        print("✗ 验证失败：__init__.py 不存在")
        return None

    print("✓ __init__.py 已复制")

    # Extract timestamp
    try:
        with open(INIT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        match = re.search(r'"last_updated":\s*"([^"]*)"', content)
        if match:
            timestamp = match.group(1)
            print(f"✓ 当前时间戳: {timestamp}")
            return timestamp
        else:
            print("⚠ 未找到 last_updated 字段")
            return None
    except Exception as e:
        print(f"✗ 验证失败：{e}")
        return None

def main():
    """Main sync process"""
    print_header("XPS to PMX 插件同步脚本")

    # Sync files
    if not sync_files():
        print("✗ 同步失败")
        sys.exit(1)

    # Update timestamp
    timestamp = update_timestamp()

    # Verify
    print()
    verify_result = verify_sync()

    print()
    print("=" * 60)
    print("✓ 同步完成！")
    print("=" * 60)
    print()
    print("【下一步】")
    print("1. 完全关闭 Blender（如果打开了的话）")
    print("2. 重新打开 Blender")
    print("3. 打开 XPS to PMX Mapper 面板")
    print("4. 在面板顶部应该看到最新的版本时间戳")
    print()
    if verify_result:
        print(f"当前版本时间戳: {verify_result}")
    print()

if __name__ == "__main__":
    main()
