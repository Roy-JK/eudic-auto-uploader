import sys

from auto_upload import log_to_file, run_uploader
from fetch_rss import ENABLE_FETCH, ENABLE_UPLOAD, fetch_rss_main


def main():
    with log_to_file() as log_file_path:
        print(f"日志文件: {log_file_path}")
        print(sys.executable)

        if ENABLE_FETCH:
            print("▶️ 开始下载任务...")
            fetch_rss_main()
        else:
            print("⏭️ 已禁用下载 (enable_fetch=false)")

        if ENABLE_UPLOAD:
            print("▶️ 开始上传任务...")
            run_uploader()
        else:
            print("⏭️ 已禁用上传 (enable_upload=false)")


if __name__ == "__main__":
    main()
