"""
这个用来扫描本地目录，检查文件是否在NAS的数据库中存在
"""
import glob
import os
import requests
import hashlib

API_BASE = "http://10.0.0.5:8083/api/search"

root = "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/"
# scan_paths = [
#     "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/照片和视频/照片-真的没备份吗",
# ]
scan_paths = [
    "/Volumes/Yumi/微信聊天记录备份",
]


def calc_sha1(path: str, buf_size: int = 1024 * 1024) -> str:
    """计算文件的 sha1 摘要"""
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            data = f.read(buf_size)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def file_exists_in_nas(file_name: str, sha1: str) -> bool:
    """
    通过 API 判断 NAS 中是否存在同名且 sha1 相同的文件。
    这里不限制 path，只用 name + hash 精确匹配。
    """
    try:
        resp = requests.get(
            API_BASE,
            params={
                "path": None,
                "name": file_name,
                "hash": sha1,
                "fuzzy": False,
            },
            timeout=10,
        )
        data = resp.json()
    except Exception as e:
        # 出错时当作未找到，避免误报为“已同步”
        print(f"\n查询 API 出错，按未同步处理: name={file_name}, sha1={sha1}, err={e}")
        return False

    # 只要有至少一条记录，就认为已经同步
    return data.get("count", 0) > 0


unsynced_files = []

for scan_path in scan_paths:
    print("*" * 50)
    print(f"扫描目录：{scan_path}")

    paths = glob.glob(f"{scan_path}/**/*", recursive=True)
    total_files = len(paths)
    current_num = 0

    for path in paths:
        current_num += 1
        print(f"\rProgress: {current_num}/{total_files}", end="")

        if os.path.isdir(path) or not os.path.exists(path):
            continue

        file_name = os.path.basename(path)

        # 先算本地 sha1
        try:
            sha1 = calc_sha1(path)
        except (OSError, PermissionError) as e:
            print(f"\n跳过无法读取的文件: {path} ({e})")
            continue

        # 调用 API 判断是否存在同名且 sha1 相同的文件
        if not file_exists_in_nas(file_name, sha1):
            unsynced_files.append(path)

print()
print("未同步文件数：", len(unsynced_files))
for p in unsynced_files:
    print(p)
