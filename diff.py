import glob
import os
import requests

path_pairs = [
    ('/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/照片和视频/20220129未整理/DCIM/Video',
     '/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/确认重复后删除/照片和视频/20220129未整理/Video'),
]

# /srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/确认重复后删除/

for path_pair in path_pairs:
    print("*" * 50)
    left_path = path_pair[0]
    right_path = path_pair[1]
    print("对比目录：\n左边：'%s'\n右边：'%s'" % (left_path, right_path))

    left_files = {}
    right_files = {}
    not_in_db = []
    same_name_same_hash = []
    same_name_different_hash = []
    left_only = []
    right_only = []

    left_paths = glob.glob('%s/**/*' % left_path, recursive=True)
    total_files = len(left_paths)
    current_num = 0
    for path in left_paths:
        current_num += 1
        print("\rProgress: %d/%d" % (current_num, total_files), end="")
        if os.path.isdir(path) or not os.path.exists(path):  # 跳过文件夹和不存在的文件
            continue
        path_name = os.path.dirname(path)
        file_name = os.path.basename(path)
        req = requests.get("http://10.0.0.5:8083/api/search", params={"path": path_name, "name": file_name, "hash": None, "fuzzy": False}).json()
        if req["count"] == 0:
            # 文件不在数据库中
            print("文件不在数据库中", path)
            not_in_db.append(path)
        elif req["count"] > 1:
            # 文件重复，不应该发生
            print("文件重复，不应该发生", req)
            exit(1)
        else:
            left_files[path[len(left_path):]] = req["file_list"][0]["hash"]

    right_paths = glob.glob('%s/**/*' % right_path, recursive=True)
    total_files = len(right_paths)
    current_num = 0
    for path in right_paths:
        current_num += 1
        print("\rProgress: %d/%d" % (current_num, total_files), end="")
        if os.path.isdir(path) or not os.path.exists(path):  # 跳过文件夹和不存在的文件
            continue
        path_name = os.path.dirname(path)
        file_name = os.path.basename(path)
        req = requests.get("http://10.0.0.5:8083/api/search", params={"path": path_name, "name": file_name, "hash": None, "fuzzy": False}).json()
        if req["count"] == 0:
            # 文件不在数据库中
            print("\n文件不在数据库中", path)
            not_in_db.append(path)
        elif req["count"] > 1:
            # 文件重复，不应该发生
            print("\n文件重复，不应该发生", req)
            exit(1)
        else:
            right_files[path[len(right_path):]] = req["file_list"][0]["hash"]

    for key in left_files.keys():
        if key not in right_files:
            left_only.append(key)
        elif left_files[key] == right_files[key]:
            same_name_same_hash.append(key)
        else:
            same_name_different_hash.append(key)
    for key in right_files.keys():
        if key not in left_files:
            right_only.append(key)
    print()
    print("相同的文件：%d 个" % len(same_name_same_hash))
    print("不同的同名文件：%d 个" % len(same_name_different_hash))
    for name in same_name_different_hash:
        print(name)
    print("左边独有文件：%d 个" % len(left_only))
    for name in left_only:
        print(name)
    print("右边独有文件：%d 个" % len(right_only))
    for name in right_only:
        print(name)
