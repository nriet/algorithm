#ifndef DBCONF_H
#define DBCONF_H

#endif // DBCONF_H


// database config
#define DATABASE_TABLE_PARTITION    "call cc(DATE_ADD(NOW(),INTERVAL 1 MONTH),'t_product_path');"
#define DATABASE_TABLE_PARTITION_MYSQL    "CALL create_partition_month(DATE_ADD(NOW(),INTERVAL 1 MONTH),'db_xx_main','t_product_path');"
#define DATABASE_INI_CONFIG         "../conf/Database/database.ini"
#define DATABASE_INI_SELECT           "DataBaseSelect"
//MySQL,KingBase
#define DATABASE_INI_TYPE           "DBType"

#define DATABASE_INI_KEY_IP         "ipaddress"
#define DATABASE_INI_KEY_PORT       "port"
#define DATABASE_INI_KEY_USERNAME   "username"
#define DATABASE_INI_KEY_USERPWD    "userpwd"
#define DATABASE_INI_KEY_DBNAME     "dbname"
#define DATABASE_INI_KEY_TIMEOUT    "timeout"

#define REDIS_INI_TYPE           "Redis"
#define REDIS_INI_KEY_IP         "ipaddress"
#define REDIS_INI_KEY_PORT       "port"
#define REDIS_INI_KEY_TIMEOUT   "timeout"
#define REDIS_INI_KEY_USERPWD    "userpwd"
