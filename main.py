"""
文件管理工具
1. 文件安全拷贝功能，拷贝后校验src和dst的sha1
2. 文件搜索功能，记录所有文件的路径到数据库中，可以根据文件路径、文件名、hash值搜索
3. 文件校验功能，可以发现本次扫描和上次扫描之间的文件增删改
4. 文件查重功能，可以发现文件hash相同的文件
5. 带简单的前端界面
"""
import glob
import os
import socket
import threading
import time

from flask import Flask, jsonify, request
from sqlalchemy import func, desc, asc, or_, not_

from config import *
from database import db, File, Metadata, Hashes, NewFiles, ChangedFiles, DeletedFiles
from utils import get_hash, get_modify_time

hostname = socket.gethostname()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///file-%s.db' % hostname
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///file-openmediavault.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db.init_app(app)

is_scanning = False
is_quick_scan = False
scan_thread = None
total_files = 0


def init():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        scan_times = Metadata.query.filter_by(name="scan_times").first()
        if not scan_times:
            db.session.add(Metadata(name="scan_times", value=0))
            db.session.commit()
        start_time = Metadata.query.filter_by(name="start_time").first()
        if not start_time:
            db.session.add(Metadata(name="start_time", value=0))
            db.session.commit()
        end_time = Metadata.query.filter_by(name="end_time").first()
        if not end_time:
            db.session.add(Metadata(name="end_time", value=0))
            db.session.commit()


def scan(quick_scan=False):
    """
    扫描文件
    :param quick_scan: 快速扫描，如果为True，则只判断文件修改时间，文件修改时间发生变化才重新计算hash
    :return:
    """
    global is_scanning, total_files, is_quick_scan
    if is_scanning:
        return
    is_scanning = True
    is_quick_scan = quick_scan
    if quick_scan:
        print("快速扫描")
    # 开始扫描
    with app.app_context():
        # 记录开始时间
        start_time = Metadata.query.filter_by(name="start_time").first()
        start_time.value = int(time.time())
        # 清空三个文件变化表
        db.session.query(NewFiles).delete()
        db.session.query(ChangedFiles).delete()
        db.session.query(DeletedFiles).delete()
        db.session.commit()
        scan_times = Metadata.query.filter_by(name="scan_times").first()
        scan_times.value += 1
        print("开始扫描，当前扫描次数：", scan_times.value)
        paths = glob.glob('%s/**/*' % ROOT, recursive=True)
        total_files = len(paths)
        print("total_files:", total_files)
        existing_files = {(file.path, file.name): file for file in File.query.all()}
        print("existing_files:", len(existing_files))
        last_commit = time.time()
        invalid_paths = []
        for path in paths:
            try:
                path.encode('utf-8')  # 尝试编码为 UTF-8
            except UnicodeEncodeError:
                safe_path = path.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')  # 处理复杂字符
                print("路径包含非法字符，跳过该文件:", safe_path)
                invalid_paths.append(safe_path)
                continue
            if DEBUG:
                print("scanning:", path)
            if os.path.isdir(path) or not os.path.exists(path):  # 跳过文件夹和不存在的文件
                continue
            path_name = os.path.dirname(path)
            if IGNORE_PATHS:  # 忽略指定文件夹
                ignore = False
                for ignore_path in IGNORE_PATHS:
                    if path_name.startswith(ignore_path):
                        ignore = True
                        break
                if ignore:
                    continue
            file_size = os.path.getsize(path)
            if IGNORE_SMALL_FILE:  # 跳过小文件
                if file_size < SMALL_FILE_SIZE:
                    continue
            modify_time = get_modify_time(path)
            file_name = os.path.basename(path)
            file = existing_files.get((path_name, file_name))
            if file:
                # 检查文件修改日期有没有变化
                if modify_time != file.modify_time:
                    print(file, "文件发生了修改", file.modify_time, "->", modify_time)
                    file_hash = get_hash(path)
                    if file_hash is None:
                        continue
                    db.session.add(ChangedFiles(
                        name=file.name, path=file.path,
                        old_size=file.size, new_size=file_size,
                        old_hash=file.hash, new_hash=file_hash,
                        old_modify_time=file.modify_time, new_modify_time=modify_time,
                    ))
                    file.modify_time = modify_time
                    file.hash = file_hash
                elif not quick_scan:  # 文件修改日期没发生变化，如果不是快速扫描，则计算hash并更新
                    file_hash = get_hash(path)
                    if file_hash is None:
                        continue
                    if file_hash != file.hash:
                        print(file, "文件修改时间没变化，但hash发生了变化", file.hash, "->", file_hash)
                        db.session.add(ChangedFiles(
                            name=file.name, path=file.path,
                            old_size=file.size, new_size=file_size,
                            old_hash=file.hash, new_hash=file_hash,
                            old_modify_time=file.modify_time, new_modify_time=modify_time,
                        ))
                        file.hash = file_hash
                file.size = file_size
                file.scan_times = scan_times.value
            else:
                # 加入新文件
                file_hash = get_hash(path)
                if file_hash is None:
                    continue
                file = File(name=file_name, path=path_name, size=file_size, hash=file_hash, modify_time=modify_time, scan_times=scan_times.value)
                print(file, "发现新文件")
                db.session.add(file)
                db.session.add(NewFiles(name=file.name, path=file.path, size=file_size, hash=file_hash))
            if time.time() - last_commit > 60:  # 每分钟commit一次
                print("commit...")
                db.session.commit()
                last_commit = time.time()
        db.session.commit()
        # 检查被删除的文件
        deleted_files = File.query.filter(File.scan_times != scan_times.value)
        for file in deleted_files:
            print(file, "文件被删除")
            db.session.add(DeletedFiles(name=file.name, path=file.path, size=file.size, hash=file.hash))
            db.session.delete(file)
        db.session.commit()
        update_hashes_table()
        # 记录结束时间
        end_time = Metadata.query.filter_by(name="end_time").first()
        end_time.value = int(time.time())
        db.session.commit()
        is_scanning = False
        if invalid_paths:
            print("本次扫描跳过了下面的文件（因为路径包含非法字符）：")
            for invalid_path in invalid_paths:
                print(invalid_path)
        print("扫描完成")


def update_hashes_table():
    """更新hashes表，用于文件查重"""
    with app.app_context():
        # 清空hashes表
        db.session.query(Hashes).delete()
        db.session.commit()
        # 写入hashes表
        query = File.query.with_entities(File.hash, func.count("*").label("count")).group_by(File.hash)
        for item in query:
            db.session.add(Hashes(hash=item.hash, count=item.count))
        db.session.commit()


def get_duplicated_files(limit=None, offset=None):
    """
    获取重复的文件
    :return: 重复文件列表，格式如下
    [
        {"hash": "hash值", "count": "重复数量", "files": [文件列表...]},
        ...
    ]
    """
    duplicated_files = []
    with app.app_context():
        # 构造后缀过滤条件
        suffix_filters = []
        for suf in DUP_IGNORE_SUFFIXES:
            # 统一处理，确保前面有点
            suffix_filters.append(File.name.like(f'%.{suf}'))
        # 构造文件名过滤条件
        filename_filter = File.name.in_(IGNORE_FILE_NAMES) if IGNORE_FILE_NAMES else None
        base_filters = [File.size > 0]
        if suffix_filters:
            base_filters.append(not_(or_(*suffix_filters)))
        if filename_filter is not None:
            base_filters.append(not_(filename_filter))
        base_file_query = File.query.filter(*base_filters)
        subquery = (
            base_file_query.with_entities(
                File.hash.label('hash'),
                func.count('*').label('count')
            )
            .group_by(File.hash)
            .having(func.count('*') >= 2)
        ).subquery()

        # 先获取总数，方便前端分页
        total = db.session.query(func.count()).select_from(subquery).scalar()
        query = db.session.query(
            subquery.c.hash,
            subquery.c.count
        ).order_by(desc(subquery.c.count))
        # 应用分页
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        for hash_row in query:
            hash_dict = {"hash": hash_row.hash, "count": hash_row.count, "files": []}
            files = File.query.filter_by(hash=hash_row.hash).order_by(desc(File.size))
            for file in files:
                hash_dict["files"].append({"path": file.path, "name": file.name})
            duplicated_files.append(hash_dict)
        return {
            "total": total,
            "items": duplicated_files,
        }


@app.route("/api/duplicated_files", methods=["GET"])
def api_duplicated_files():
    """查询重复文件"""
    # 读取 URL 参数
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", type=int)
    # 如果前端用 page / page_size，也做个兼容
    page = request.args.get("page", type=int)
    page_size = request.args.get("page_size", type=int)
    if page is not None and page_size is not None:
        # 页码从1开始
        offset = (page - 1) * page_size
        limit = page_size
    result = get_duplicated_files(limit=limit, offset=offset)
    return jsonify(result)


@app.route("/api/new_files", methods=["GET"])
def api_new_files():
    """查询新增文件"""
    file_list = []
    with app.app_context():
        for file in NewFiles.query.all():
            file_list.append({"name": file.name, "path": file.path, "hash": file.hash, "size": file.size})
    return jsonify({"file_list": file_list, "count": len(file_list)})


@app.route("/api/deleted_files", methods=["GET"])
def api_deleted_files():
    """查询删除文件"""
    file_list = []
    with app.app_context():
        for file in DeletedFiles.query.all():
            file_list.append({"name": file.name, "path": file.path, "hash": file.hash, "size": file.size})
    return jsonify({"file_list": file_list, "count": len(file_list)})


@app.route("/api/changed_files", methods=["GET"])
def api_changed_files():
    """查询修改文件"""
    file_list = []
    with app.app_context():
        for file in ChangedFiles.query.all():
            file_list.append({"name": file.name, "path": file.path,
                              "old_hash": file.old_hash, "old_size": file.old_size,
                              "new_hash": file.new_hash, "new_size": file.new_size,
                              "old_modify_time": file.old_modify_time, "new_modify_time": file.new_modify_time})
    return jsonify({"file_list": file_list, "count": len(file_list)})


@app.route("/api/scan", methods=["GET"])
def api_scan():
    """开始扫描"""
    global is_scanning, scan_thread
    if not is_scanning:
        quick_scan = False
        print(request.args.get('quick_scan'))
        if request.args.get('quick_scan') == "1":
            quick_scan = True
        scan_thread = threading.Thread(target=scan, args=(quick_scan,))
        scan_thread.start()
        return jsonify({"status": "start scanning"})
    return jsonify({"status": "already scanning"})


@app.route("/api/scan_status", methods=["GET"])
def api_scan_status():
    """扫描状态"""
    global is_scanning, total_files, is_quick_scan
    with app.app_context():
        start_time = Metadata.query.filter_by(name="start_time").first()
        new_files = NewFiles.query.with_entities(func.count(NewFiles.id).label("count")).first().count
        deleted_files = DeletedFiles.query.with_entities(func.count(DeletedFiles.id).label("count")).first().count
        changed_files = ChangedFiles.query.with_entities(func.count(ChangedFiles.id).label("count")).first().count
        if is_scanning:
            scan_times = Metadata.query.filter_by(name="scan_times").first()
            scanned = File.query.filter_by(scan_times=scan_times.value).count()
            if total_files == 0:
                progress = 0
            else:
                progress = round(scanned / total_files, 2)
            return jsonify({"status": is_scanning, "quick_scan": is_quick_scan,
                            "total": total_files, "remain": total_files - scanned,
                            "progress": progress, "start_time": start_time.value,
                            "new_files": new_files, "deleted_files": deleted_files, "changed_files": changed_files})
        end_time = Metadata.query.filter_by(name="end_time").first()
        total_size = File.query.with_entities(func.sum(File.size).label("size")).first()
        total_files = File.query.with_entities(func.count(File.id).label("count")).first().count
    return jsonify({"status": is_scanning, "start_time": start_time.value, "end_time": end_time.value,
                    "file": total_files, "size": total_size.size,
                    "new_files": new_files, "deleted_files": deleted_files, "changed_files": changed_files})


@app.route("/api/search", methods=["GET"])
def api_search():
    """搜索"""
    path = request.args.get('path')
    name = request.args.get('name')
    hash = request.args.get('hash')
    fuzzy = request.args.get('fuzzy') == "true"  # 模糊搜索
    file_list = []
    with app.app_context():
        query = File.query
        if path:
            if fuzzy:
                query = query.filter(File.path.like("%" + path + "%"))
            else:
                query = query.filter_by(path=path)
        if name:
            if fuzzy:
                query = query.filter(File.name.like("%" + name + "%"))
            else:
                query = query.filter_by(name=name)
        if hash:
            if fuzzy:
                query = query.filter(File.hash.like("%" + hash + "%"))
            else:
                query = query.filter_by(hash=hash)
        files = query.order_by(asc(File.path), asc(File.name))
        for file in files:
            file_list.append({"path": file.path, "name": file.name, "hash": file.hash, "size": file.size, "modify_time": file.modify_time})
    return jsonify({"file_list": file_list, "count": len(file_list)})


@app.route("/", methods=["GET"])
def index_page():
    """主页"""
    return app.send_static_file("index.html")


if __name__ == '__main__':
    init()
    # scan()
    # print(get_duplicated_files())
    app.run(port=8083, host="0.0.0.0")
