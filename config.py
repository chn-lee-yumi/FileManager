ROOT = "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym"  # 末尾不要加/
DEBUG = True

IGNORE_SMALL_FILE = False
SMALL_FILE_SIZE = 128 * 1024

IGNORE_PATHS = ("/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/mysql_data",
                "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/prometheus/prometheus-data",
                "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/学习和工作/Android/ROM制作/制作环境/cygwin",
                "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/学习和工作/Linux/anmpp/android.pgsql",
                "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/github",
                "/srv/dev-disk-by-uuid-5b249b15-24f2-4796-a353-5ba789dc1e45/lym/kodbox",
                )  # 末尾不要加/

# 查重时要忽略的后缀（不含点），例如: "ts" 表示 "*.ts"
DUP_IGNORE_SUFFIXES = (
    "ts",
    "json",
    "flow",
    "less",
    "txt",
    "js",
    "mvfrm",
    "bnf",
)

# 查重时要忽略的完整文件名（区分大小写）
DUP_IGNORE_FILE_NAMES = (
    "LICENSE",
    "license",
)
