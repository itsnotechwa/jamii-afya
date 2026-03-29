import pymysql
pymysql.__version__ = "2.2.1"   # satisfy Django 6's mysqlclient version gate
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()
