import glob
import hashlib
import os.path
import shutil
import time
from datetime import datetime


def get_modify_time(path):
    """
    读取文件修改时间
    :param path: 文件路径
    :return: datetime
    """
    return datetime.fromtimestamp(os.path.getmtime(path))


def get_hash(path):
    """
    计算hash
    :param path: 文件路径
    :return: 十六进制字符串
    """
    _hash = hashlib.sha1()
    try:
        with open(path, "rb") as f:
            while True:
                data = f.read(1048576)
                if not data:
                    break
                _hash.update(data)
    except Exception as e:
        print("计算hash出错：", repr(e))
        return None
    return _hash.hexdigest()


def get_hash_md5(path):
    """
    计算hash
    :param path: 文件路径
    :return: 十六进制字符串
    """
    _hash = hashlib.md5()
    try:
        with open(path, "rb") as f:
            while True:
                data = f.read(1048576)
                if not data:
                    break
                _hash.update(data)
    except Exception as e:
        print("计算hash出错：", repr(e))
        return None
    return _hash.hexdigest()


def hash_speed_test():
    """
    测试hash速度
    :return:
    """
    test_file = "100MB.tmp"
    get_hash(test_file)
    get_hash_md5(test_file)

    t0 = time.time()
    for i in range(10):
        get_hash(test_file)
    print("SHA1: %.2f MB/s" % (100 * 10 / (time.time() - t0)))

    t0 = time.time()
    for i in range(10):
        get_hash_md5(test_file)
    print("MD5: %.2f MB/s" % (100 * 10 / (time.time() - t0)))

    t0 = time.time()
    for i in range(10):
        get_hash(test_file)
    print("SHA1: %.2f MB/s" % (100 * 10 / (time.time() - t0)))

    t0 = time.time()
    for i in range(10):
        get_hash_md5(test_file)
    print("MD5: %.2f MB/s" % (100 * 10 / (time.time() - t0)))


def safe_copy(src, dst, check=True):
    """
    拷贝文件后进行hash校验
    :param src: 源文件路径
    :param dst: 目标路径
    :param check: 是否校验
    :return: 校验通过返回0，否则返回1
    """
    if check:
        src_hash = get_hash(src)
        shutil.copy(src, dst)
        dst_hash = get_hash(dst)
        if src_hash != dst_hash:
            print("文件复制后校验出错！")
            return 1
    else:
        shutil.copy(src, dst)
    return 0


def safe_merge(src, dst, check_same=False):
    """
    将src文件夹的内容合并到dst文件夹，即将src文件夹内dst文件夹不存在的文件复制到dst文件夹内。如有文件同名不同hash，则提示。
    :param src: 源文件夹路径
    :param dst: 目标文件夹路径
    :param check_same: 是否校验同名文件
    :return:
    """
    src_files = set(map(lambda x: os.path.basename(x), glob.glob(src + "/*")))
    dst_files = set(map(lambda x: os.path.basename(x), glob.glob(dst + "/*")))
    print(len(src_files), len(dst_files))
    # 校验相同的
    if check_same:
        same = src_files & dst_files
        for file in same:
            hash_src = get_hash(src + "/" + file)
            hash_dst = get_hash(dst + "/" + file)
            if hash_src != hash_dst:
                print("两个同名文件hash不同：", file)
    # 复制
    diff = src_files - dst_files
    for file in diff:
        print("copy", src + "/" + file, "->", dst + "/" + file)
        # safe_copy(src + "/" + file, dst + "/" + file, check=False)


if __name__ == '__main__':
    # hash_hex = get_hash("/Users/liyumin/Downloads/android-x86_64-9.0-r2.iso")
    # print(hash_hex)
    safe_merge("/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/照片和视频/手机相册/全景相册",
               "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/照片和视频/手机相册/相机相册")
