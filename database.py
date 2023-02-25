from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)  # 文件名
    path = db.Column(db.String(4096), index=True)  # 文件路径
    hash = db.Column(db.String(40), index=True)  # hash值
    size = db.Column(db.Integer)  # 文件大小
    modify_time = db.Column(db.DateTime)  # 文件修改时间
    scan_times = db.Column(db.Integer, index=True)  # 扫描次数

    def __repr__(self):
        return '<File %s/%s %s %d %r>' % (self.path, self.name, self.hash, self.size, self.modify_time)

    def to_dict(self):
        return {"path": self.path, "name": self.name, "hash": self.hash, "size": self.size, "modify_time": self.modify_time}


class Metadata(db.Model):
    name = db.Column(db.String(255), primary_key=True)  # 元数据名
    value = db.Column(db.Integer)  # 元数据值


class Hashes(db.Model):
    hash = db.Column(db.String(40), primary_key=True, index=True)  # hash值
    count = db.Column(db.Integer, index=True)  # hash值相同的文件数量

    def __repr__(self):
        return '<Hashes %s %d>' % (self.hash, self.count)


class NewFiles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)  # 文件名
    path = db.Column(db.String(4096), index=True)  # 文件路径
    hash = db.Column(db.String(40))  # hash值
    size = db.Column(db.Integer)  # 文件大小


class ChangedFiles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)  # 文件名
    path = db.Column(db.String(4096), index=True)  # 文件路径
    old_hash = db.Column(db.String(40))  # hash值
    old_size = db.Column(db.Integer)  # 文件大小
    new_hash = db.Column(db.String(40))  # hash值
    new_size = db.Column(db.Integer)  # 文件大小
    old_modify_time = db.Column(db.DateTime)  # 文件修改时间
    new_modify_time = db.Column(db.DateTime)  # 文件修改时间


class DeletedFiles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), index=True)  # 文件名
    path = db.Column(db.String(4096), index=True)  # 文件路径
    hash = db.Column(db.String(40))  # hash值
    size = db.Column(db.Integer)  # 文件大小
