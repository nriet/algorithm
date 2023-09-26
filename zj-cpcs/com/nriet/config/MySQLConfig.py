from pymysql.cursors import DictCursor

config1 = {
        'host': 'njbox.myds.me',
        'port': 10000,
        'database': 'cipas',
        'user': 'root',
        'passwd': 'Nriet123!@#',
        'charset': 'utf8',
        'cursorclass': DictCursor
    }
config = {
        'host': '10.20.70.62',
        'port': 3306,
        'database': 'seaclimate',
        'user': 'root',
        'passwd': 'seasea',
        'charset': 'utf8',
        'cursorclass': DictCursor
    }

config_cluster = {
        'host': '10.40.24.41',
        'port': 3306,
        'database': 'seaclimate',
        'user': 'root',
        'passwd': 'Nriet!@#',
        'charset': 'utf8',
        'cursorclass': DictCursor
    }
config_data_monitor = {
        'host': '10.40.24.33',
        'port': 3306,
        'database': 'default',
        'user': 'root',
        'passwd': 'Nriet!@#123',
        'charset': 'utf8',
        'cursorclass': DictCursor
    }