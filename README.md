# nuScenes 下载助手（nuscenes_HELP）

## 项目简介
用于辅助下载 nuScenes 数据集压缩包：脚本会先通过官方接口获取预签名下载链接，然后按你的选择下载并进行 MD5 校验。

## 功能特性
- 交互式选择要下载的文件（或一键全选）
- 下载进度条显示
- 自动校验 MD5；已完整下载的文件会自动跳过
- 校验失败可选择重下
- `setup.py` 可选：自动创建 `.venv` 并检查依赖后启动主脚本

## 安装方法
```bash
pip install -r requirements.txt
```

也可以直接运行启动脚本（会询问是否创建/使用 `.venv` 并检查依赖）：
```bash
python setup.py
```

## 使用方法

### 1) 获取 nuScenes Token
1. 登录 nuScenes 官网并进入下载相关页面。
2. 打开浏览器开发者工具（F12）→ Network。
3. 找到请求头里带 `Authorization: Bearer ...` 的请求，复制 `Bearer` 后面的 token 内容。

### 2) 配置 Token（推荐两种方式）

方式 A：环境变量（不会写入文件，最安全）
- Windows PowerShell：
  ```powershell
  $env:NUSCENES_TOKEN="YOUR_TOKEN"
  ```
- Windows CMD：
  ```bat
  set NUSCENES_TOKEN=YOUR_TOKEN
  ```
- Linux/macOS：
  ```bash
  export NUSCENES_TOKEN="YOUR_TOKEN"
  ```

方式 B：`config.json`（已在 `.gitignore` 中忽略，不会被提交）
1. 复制 `config.example.json` 为 `config.json`
2. 将 `bearer_token` 改为你的 token

可选配置项：
- `region`：默认 `asia`
- `output_dir`：默认 `./output_files`

### 3) 运行
```bash
python src/download_interactive.py
```

然后根据提示输入：
- `all`：下载全部
- `0 1 5`：下载指定编号
- `q`：退出

## 免责声明
本项目仅用于辅助下载 nuScenes 数据集文件，所有数据集版权归 nuScenes 所有；请确保你已同意并遵守 nuScenes 的相关许可与使用条款，严禁将数据集文件重新分发或用于任何未授权用途。
"# nuscenes-batch-downloader" 
