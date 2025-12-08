import sys
import os
import re
import requests
import feedparser
import pandas as pd
import yaml  # <--- [新增] 必须安装: pip install PyYAML
from dateutil import parser as date_parser
from urllib.parse import urlparse
import shutil

# ================= 配置加载逻辑 (Config Loading) =================

CONFIG_FILE = "config.yaml"


def load_config():
    """
    读取 YAML 配置文件
    返回一个 Python 字典，例如: {'rss_feeds': {...}, 'year_from': 2025}
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"⚠️  警告: 找不到配置文件 {CONFIG_FILE}，将使用代码内的默认值。")
        return {}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            # yaml.safe_load 是将 yaml 文本转为 python 字典的核心函数
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return {}


# 1. 在模块加载时，立即执行读取
_config = load_config()

# 2. 初始化全局变量
# 这里实现了 yaml(小写) 到 python(大写) 的映射
# 如果 yaml 里没写或者读不到，就用逗号后面的默认值
RSS_FEEDS = _config.get("rss_feeds", {})
YEAR_FROM = _config.get("year_from", 2025)
LATEST_NUM = _config.get("latest_num", 2)
DOWNLOAD_FOLDER = _config.get("download_folder", "rss_download")

# ================= 工具函数 =================


def parse_duration(dur_raw: str) -> str:
    if not dur_raw:
        return ""
    parts = dur_raw.split(":")
    try:
        parts = [int(p) for p in parts]
        total_sec = sum([x * 60**i for i, x in enumerate(reversed(parts))])
        m, s = divmod(total_sec, 60)
        return f"{m}:{s:02d}"
    except ValueError:
        return dur_raw


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:"*?<>|]+', "", name).strip()
    return re.sub(r"\s+", "-", name)


def parse_rss(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        feed = feedparser.parse(response.content)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    rows = []
    for entry in feed.entries:
        raw_date = entry.get("published", entry.get("pubDate", ""))
        try:
            dt = date_parser.parse(raw_date)
            date_str = dt.strftime("%Y-%m-%d")
            file_date = dt.strftime("%Y%m%d")
        except Exception:
            date_str = file_date = ""

        title = entry.get("title", "").strip()
        summary = entry.get("summary", "").strip()
        duration_fmt = parse_duration(entry.get("itunes_duration", ""))

        audio_link = ""
        if entry.get("enclosures"):
            audio_link = entry.enclosures[0].get("href", "")
        link = audio_link or entry.get("link", "")

        rows.append(
            {
                "日期": date_str,
                "文件日期": file_date,
                "题目": title,
                "简介": summary,
                "时长": duration_fmt,
                "链接": link,
            }
        )
    return rows


def download_audios(rows, subfolder, year_limit, num_limit):
    """
    下载逻辑：接收 year_limit 和 num_limit 参数，不再依赖全局变量
    """
    out_dir = os.path.join(DOWNLOAD_FOLDER, subfolder)
    os.makedirs(out_dir, exist_ok=True)

    filtered_rows = [
        item
        for item in rows
        if item["链接"]
        and item["文件日期"][:4].isdigit()
        and int(item["文件日期"][:4]) >= year_limit
    ]
    filtered_rows.sort(key=lambda x: x["文件日期"], reverse=True)

    if num_limit != -1:
        filtered_rows = filtered_rows[:num_limit]

    for item in filtered_rows:
        datepart = item["文件日期"]
        titlepart = sanitize_filename(item["题目"])
        ext = os.path.splitext(urlparse(item["链接"]).path)[1] or ".mp3"
        fname = f"{datepart}-{titlepart}{ext}"
        dest = os.path.join(out_dir, fname)

        if os.path.exists(dest):
            continue

        print(f"Downloading → {fname}")
        try:
            resp = requests.get(item["链接"], stream=True, timeout=60)
            resp.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
        except Exception as e:
            print(f"  ✗ failed: {e}")


# ================= 主入口 (支持传参覆盖 YAML 配置) =================


def fetch_rss_main(
    target_feeds=None, year_from=None, latest_num=None, clean_folder=True
):
    """
    参数说明:
    - target_feeds: (Dict) 自定义下载列表。如果不传，则使用 YAML 中的全局配置。
    - year_from: (Int) 自定义年份。如果不传，则使用 YAML 配置。
    - latest_num: (Int) 自定义数量。如果不传，则使用 YAML 配置。
    - clean_folder: (Bool) 是否清空目录。默认为 True。
    """

    # 1. 优先级逻辑：函数参数 > YAML全局配置
    feeds_to_use = target_feeds if target_feeds is not None else RSS_FEEDS
    year_to_use = year_from if year_from is not None else YEAR_FROM
    num_to_use = latest_num if latest_num is not None else LATEST_NUM

    # 2. 清理目录逻辑
    if clean_folder and os.path.exists(DOWNLOAD_FOLDER):
        print(f"🧹 检测到旧目录 [{DOWNLOAD_FOLDER}]，正在彻底删除...")
        try:
            shutil.rmtree(DOWNLOAD_FOLDER)
            print("✅ 旧目录已清理完成")
        except Exception as e:
            print(f"⚠️ 删除旧目录失败: {e}")
        print("")

    print(f"=== 开始 RSS 下载任务 (年份>={year_to_use}, 数量={num_to_use}) ===")

    for name, url in feeds_to_use.items():
        print(f"\n📥 处理 {name} ...")
        data = parse_rss(url)
        if not data:
            print(f"⚠️  无数据: {name}")
            continue

        out_dir = os.path.join(DOWNLOAD_FOLDER, name)
        os.makedirs(out_dir, exist_ok=True)

        df = pd.DataFrame(data)
        excel_path = os.path.join(out_dir, f"{name}.xlsx")
        df.to_excel(excel_path, index=False)

        # 传入确定好的参数
        download_audios(
            data, subfolder=name, year_limit=year_to_use, num_limit=num_to_use
        )
        print(f"✅ {name} 处理完成")

    print("\n=== 下载任务结束 ===")


if __name__ == "__main__":
    # 无参数运行，则使用 config.yaml 的配置
    # fetch_rss_main()

    fetch_rss_main(
    target_feeds={
        "Disney Magic of Storytelling": "https://feeds.megaphone.fm/ESP4559331002"
    },
    year_from=2024,
    latest_num=10
)
