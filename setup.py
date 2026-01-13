import os
import sys
import subprocess
import venv
import platform

# 定义依赖列表
REQUIRED_PACKAGES = ["requests", "tqdm"]
# 定义主程序路径 (相对于根目录)
MAIN_SCRIPT_PATH = os.path.join("src", "download_interactive.py")
# 定义虚拟环境目录名称
VENV_DIR = ".venv"

def get_venv_python_executable():
    """获取虚拟环境中的 Python解释器路径"""
    if platform.system() == "Windows":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    else:
        return os.path.join(VENV_DIR, "bin", "python")

def check_and_install_dependencies(python_exec):
    """检查并安装依赖"""
    print(f"\n[环境检查] 正在检查依赖库: {', '.join(REQUIRED_PACKAGES)}...")
    
    # 构造 pip list 命令
    try:
        result = subprocess.check_output([python_exec, "-m", "pip", "list"], encoding='utf-8')
        missing_packages = [pkg for pkg in REQUIRED_PACKAGES if pkg.lower() not in result.lower()]
        
        if not missing_packages:
            print("[环境检查] ✅ 所有依赖已安装。")
            return
        
        print(f"[环境检查] ❌ 缺少依赖: {', '.join(missing_packages)}")
        choice = input(f"是否立即安装这些依赖? (y/n): ").strip().lower()
        if choice == 'y':
            subprocess.check_call([python_exec, "-m", "pip", "install"] + missing_packages + ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
            print("[环境检查] ✅ 依赖安装完成。")
        else:
            print("[提示] 未安装依赖，程序可能无法运行。")
    except subprocess.CalledProcessError as e:
        print(f"[错误] 检查依赖失败: {e}")

def main():
    print("="*50)
    print("      NuScenes 下载器启动向导 (交互模式)")
    print("="*50)

    # 1. 虚拟环境检测与创建
    current_python = sys.executable
    
    # 检查当前是否已经在 venv 中运行 (通过 sys.prefix 判断)
    in_venv = (sys.prefix != sys.base_prefix)
    
    target_python = current_python

    if not in_venv:
        if os.path.exists(VENV_DIR):
            print(f"[环境检查] 发现已存在的虚拟环境: {VENV_DIR}")
            use_venv = input("是否使用该虚拟环境运行脚本? (y/n) [推荐 y]: ").strip().lower()
            if use_venv != 'n':
                target_python = get_venv_python_executable()
        else:
            print(f"[环境检查] 未检测到虚拟环境。")
            create_venv = input(f"是否需要创建一个新的虚拟环境 ({VENV_DIR})? (y/n) [推荐 y]: ").strip().lower()
            if create_venv != 'n':
                print(f"[正在创建] 创建虚拟环境 {VENV_DIR}，请稍候...")
                venv.create(VENV_DIR, with_pip=True)
                print("[创建成功] 虚拟环境已就绪。")
                target_python = get_venv_python_executable()

    # 2. 依赖检查与安装 (使用目标 Python 解释器)
    if os.path.exists(target_python):
        check_and_install_dependencies(target_python)
    else:
        print(f"[错误] 找不到 Python 解释器: {target_python}")
        return

    # 3. 启动主程序
    if os.path.exists(MAIN_SCRIPT_PATH):
        print("\n" + "="*50)
        print("🚀 正在启动下载主程序...")
        print("="*50 + "\n")
        try:
            # 使用选定的 Python 解释器启动子进程
            subprocess.call([target_python, MAIN_SCRIPT_PATH])
        except KeyboardInterrupt:
            print("\n[用户取消] 程序已退出。")
    else:
        print(f"[错误] 找不到主程序文件: {MAIN_SCRIPT_PATH}")

if __name__ == "__main__":
    main()