import os
import glob
import piexif

photo_dir = "/Users/liyumin/待备份/微信"

for file_path in glob.glob(f"{photo_dir}/*.jpg"):
    # 读取exif信息
    try:
        exif_dict = piexif.load(file_path)
        if "Exif" in exif_dict:
            # 判断是否有Create Date信息
            if piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
                create_date = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode("utf-8").replace(":", "").replace(" ", "_")
                # 获取文件名
                file_name = os.path.basename(file_path)
                # 重命名文件
                new_name = f"{create_date}_{file_name}"
                os.rename(file_path, os.path.join(photo_dir, new_name))
    except Exception as e:
        print(file_path, repr(e))
