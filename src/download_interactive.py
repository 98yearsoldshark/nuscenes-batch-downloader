import requests
import os
import hashlib
import json
from tqdm import tqdm

# ================= 配置说明 =================
# 不要在代码里硬编码 Token，推荐：
# 1) 环境变量：NUSCENES_TOKEN
# 2) 配置文件：config.json（已在 .gitignore 中忽略）
#    - bearer_token: 你的 token
#    - region: 'asia' 等（默认 asia）
#    - output_dir: 下载保存目录（默认 ./output_files）
# ===========================================

DEFAULT_CONFIG_PATH = "config.json"
DEFAULT_OUTPUT_DIR = "./output_files"
DEFAULT_REGION = "asia"

ENV_TOKEN_KEY = "NUSCENES_TOKEN"
ENV_REGION_KEY = "NUSCENES_REGION"
ENV_OUTPUT_DIR_KEY = "NUSCENES_OUTPUT_DIR"

OUTPUT_DIR = DEFAULT_OUTPUT_DIR
REGION = DEFAULT_REGION

# 完整的文件列表和MD5
FILES_CONFIG = {
    "v1.0-test_meta.tgz": "b0263f5c41b780a5a10ede2da99539eb",
    "v1.0-test_blobs.tgz": "e065445b6019ecc15c70ad9d99c47b33",
    "v1.0-trainval01_blobs.tgz": "cbf32d2ea6996fc599b32f724e7ce8f2",
    "v1.0-trainval02_blobs.tgz": "aeecea4878ec3831d316b382bb2f72da",
    "v1.0-trainval03_blobs.tgz": "595c29528351060f94c935e3aaf7b995",
    "v1.0-trainval04_blobs.tgz": "b55eae9b4aa786b478858a3fc92fb72d",
    "v1.0-trainval05_blobs.tgz": "1c815ed607a11be7446dcd4ba0e71ed0",
    "v1.0-trainval06_blobs.tgz": "7273eeea36e712be290472859063a678",
    "v1.0-trainval07_blobs.tgz": "46674d2b2b852b7a857d2c9a87fc755f",
    "v1.0-trainval08_blobs.tgz": "37524bd4edee2ab99678909334313adf",
    "v1.0-trainval09_blobs.tgz": "a7fcd6d9c0934e4052005aa0b84615c0",
    "v1.0-trainval10_blobs.tgz": "31e795f2c13f62533c727119b822d739",
    "v1.0-trainval_meta.tgz": "537d3954ec34e5bcb89a35d4f6fb0d4a",
}

def load_config(path=DEFAULT_CONFIG_PATH):
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        return json.loads(raw) if raw else {}
    except Exception as e:
        print(f"[WARN] 读取配置文件失败: {path} ({e})")
        return {}

def resolve_settings():
    config = load_config()

    token = (os.getenv(ENV_TOKEN_KEY) or config.get("bearer_token") or config.get("token") or "").strip()
    region = (os.getenv(ENV_REGION_KEY) or config.get("region") or DEFAULT_REGION).strip() or DEFAULT_REGION
    output_dir = (os.getenv(ENV_OUTPUT_DIR_KEY) or config.get("output_dir") or DEFAULT_OUTPUT_DIR).strip() or DEFAULT_OUTPUT_DIR

    if not token:
        token = input("请输入 nuScenes Bearer Token（不会写入文件）: ").strip()
    if not token:
        raise ValueError("Token 为空，请先通过环境变量或 config.json 配置。")

    return token, region, output_dir

def get_headers(bearer_token):
    return {
        'Authorization': f'Bearer {bearer_token}',
        'Content-Type': 'application/json',
    }

def stage_1_probe_urls(bearer_token):
    """第一阶段：查看哪些可以下载 (获取下载链接)"""
    print(f"\n--- [阶段 1/3] 正在探测服务器资源 (Region: {REGION}) ---")
    valid_urls = {}
    
    headers = get_headers(bearer_token)
    # 增加一个 tqdm 进度条显示探测进度
    pbar = tqdm(FILES_CONFIG.items(), desc="获取下载链接", unit="file")
    
    for filename, md5 in pbar:
        api_url = f'https://o9k5xn5546.execute-api.us-east-1.amazonaws.com/v1/archives/v1.0/{filename}?region={REGION}&project=nuScenes'
        try:
            # 设置超时，防止卡死
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'url' in data:
                    valid_urls[filename] = {
                        'url': data['url'],
                        'md5': md5,
                        'local_path': os.path.join(OUTPUT_DIR, filename)
                    }
            elif response.status_code == 403 or response.status_code == 401:
                pbar.write(f"❌ {filename}: 认证失败 (Token可能过期)")
            else:
                pbar.write(f"⚠️ {filename}: 请求错误 code {response.status_code}")
        except Exception as e:
            pbar.write(f"❌ {filename}: 网络连接错误")
    
    print(f"\n✅ 探测完成。成功获取 {len(valid_urls)}/{len(FILES_CONFIG)} 个文件的下载地址。")
    return valid_urls

def stage_2_select_files(valid_urls):
    """第二阶段：用户选择下载列表"""
    if not valid_urls:
        print("没有可用的下载链接，请检查 Token 或网络。程序退出。")
        return []

    print(f"\n--- [阶段 2/3] 选择要下载的文件 ---")
    file_list = list(valid_urls.keys())
    
    # 打印菜单
    print(f"{'ID':<4} | {'文件名':<30} | {'状态'}")
    print("-" * 50)
    for idx, name in enumerate(file_list):
        local_path = valid_urls[name]['local_path']
        status = "已存在" if os.path.exists(local_path) else "未下载"
        print(f"{idx:<4} | {name:<30} | {status}")
    
    print("-" * 50)
    print("操作提示:")
    print("  - 输入 'all' 下载所有文件")
    print("  - 输入 ID 数字 (用空格分隔) 下载指定文件 (例如: 0 1 5)")
    print("  - 输入 'q' 退出")
    
    choice = input("\n请输入您的选择: ").strip().lower()
    
    selected_files = []
    
    if choice == 'q':
        return []
    elif choice == 'all':
        selected_files = file_list
    else:
        try:
            indices = choice.split()
            for i in indices:
                idx = int(i)
                if 0 <= idx < len(file_list):
                    selected_files.append(file_list[idx])
                else:
                    print(f"⚠️ 跳过无效 ID: {idx}")
        except ValueError:
            print("❌ 输入格式错误，请只输入数字。")
            return []
            
    print(f"✅ 已选择 {len(selected_files)} 个文件准备下载/校验。")
    return selected_files

def check_md5(filepath, expected_md5):
    """计算并比对 MD5"""
    print(f"正在校验完整性: {os.path.basename(filepath)} ...")
    md5obj = hashlib.md5()
    file_size = os.path.getsize(filepath)
    
    # 使用进度条显示校验过程
    with open(filepath, 'rb') as f:
        with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, desc="Verify", ascii=True) as pbar:
            for chunk in iter(lambda: f.read(4096), b""):
                md5obj.update(chunk)
                pbar.update(len(chunk))
                
    current_md5 = md5obj.hexdigest()
    return current_md5 == expected_md5

def stage_3_download_and_verify(selected_names, valid_urls):
    """第三阶段：下载并校验"""
    print(f"\n--- [阶段 3/3] 开始下载与验证 ---")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    for name in selected_names:
        info = valid_urls[name]
        url = info['url']
        save_path = info['local_path']
        expected_md5 = info['md5']
        
        # 1. 检查文件是否存在
        if os.path.exists(save_path):
            print(f"\n📁 文件已存在: {name}")
            # 询问是否覆盖或仅校验
            # 为了自动化，这里逻辑设为：存在则直接校验，校验失败则询问重下
            if check_md5(save_path, expected_md5):
                print(f"✅ {name} 校验通过 (无需重新下载)")
                continue
            else:
                print(f"❌ {name} 校验失败 (文件损坏)")
                retry = input("是否重新下载该文件? (y/n): ").lower()
                if retry != 'y':
                    continue
                # 删除旧文件准备重下
                os.remove(save_path)
        
        # 2. 下载文件
        print(f"\n⬇️ 正在下载: {name}")
        try:
            response = requests.get(url, stream=True)
            # 处理 tgz 可能变成 tar 的情况 (AWS 特性)
            content_type = response.headers.get('Content-Type', '')
            if content_type == 'application/x-tar' and save_path.endswith('.tgz'):
                save_path = save_path.replace('.tgz', '.tar')
            
            total_size = int(response.headers.get('Content-Length', 0))
            
            with open(save_path, 'wb') as file, tqdm(
                total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc=name, ascii=True
            ) as pbar:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
                        pbar.update(len(chunk))
            
            # 3. 下载后立即校验
            if check_md5(save_path, expected_md5):
                print(f"✅ {name} 下载并校验成功！")
            else:
                print(f"❌ {name} 下载后校验失败，请检查网络稳定性。")
                
        except Exception as e:
            print(f"❌ 下载出错 {name}: {e}")

def main():
    global OUTPUT_DIR, REGION

    try:
        bearer_token, region, output_dir = resolve_settings()
    except Exception as e:
        print(f"[ERROR] {e}")
        return

    REGION = region
    OUTPUT_DIR = output_dir
    print(f"当前配置: region={REGION}, output_dir={OUTPUT_DIR}")

    # 阶段 1
    valid_urls = stage_1_probe_urls(bearer_token)
    
    # 阶段 2
    selected_files = stage_2_select_files(valid_urls)
    
    # 阶段 3
    if selected_files:
        stage_3_download_and_verify(selected_files, valid_urls)
    else:
        print("未选择任何文件。")
    
    print("\n所有任务结束。")
    input("按回车键退出...")

if __name__ == "__main__":
    main()
