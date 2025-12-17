"""
这个用来扫描本地目录，检查文件是否在NAS的数据库中存在
"""
import glob
import os
import requests

root = "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/"
# scan_paths = [
#     "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/照片和视频/照片-真的没备份吗",
# ]
scan_paths = [
    "/Volumes/NO NAME/DCIM",
]

for scan_path in scan_paths:
    print("*" * 50)
    print("检查目录：'%s'" % scan_path)

    not_in_db = []
    single_file = []
    dup_files = []

    paths = glob.glob('%s/**/*' % scan_path, recursive=True)
    total_files = len(paths)
    current_num = 0
    for path in paths:
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
        else:
            hash = req["file_list"][0]["hash"]
            req = requests.get("http://10.0.0.5:8083/api/search", params={"path": None, "name": None, "hash": hash, "fuzzy": False}).json()
            if req["count"] > 1:
                # 文件重复
                item = [path[len(scan_path):]]
                for file in req['file_list']:
                    if file['path'] == path_name:
                        continue
                    else:
                        item.append((file['path'] + '/' + file["name"])[len(root):])
                dup_files.append(item)
            else:
                # 单个文件
                single_file.append(path[len(scan_path):])

    print()
    print("不重复文件数：", len(single_file))
    for file in single_file:
        print(file)
    print("重复文件数：", len(dup_files))
    for file in dup_files:
        print(file)

    # with open("dup_files.txt", "w") as f:
    #     for file in dup_files:
    #         f.write(scan_path + file[0] + "\n")
    # 删除命令：while read line; do rm "$line"; done < dup_files.txt
