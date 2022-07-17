#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import datetime
import MySQLdb
import collections
import codecs

from taoics.common.util.mysql.mysqllib import MySQL
from taoics.tardys import config


#############################################################################
__USER = config.get("database", "user")
__PASSWD = open(config.get("database", "passwd"), "r").readline().strip()
__HOST = config.get("database", "host")
__DB = config.get("database", "header")


#############################################################################
def execute(cur, query):
    print(query, file=os.sys.stderr)
    cur.execute(query)
    ret = cur.fetchall()
    print(ret, file=os.sys.stderr)
    return ret


##########################################################################
def read_file(infile, delimiter="\t"):
    
    # Loads data for creating table.
    data = []
    for line in codecs.open(infile, "r", "shift-jis"):
        print(line.encode("utf-8"))
#        if line.startswith("#"):
#            continue

        line = line.split(delimiter)

        if line[-1].endswith("\n"):
            line[-1] = line[-1].replace("\n", "")

        line = [val.strip() for val in line]

        if "".join(line) == "":  # empty line
            continue

        print(line)
        data.append(line)

    del data[0]  # deletes the header line.

    return data


def create_table(table_name, data):
    # Writes data into MySQL.
    dt = datetime.datetime.utcnow()
    dt = dt.strftime(MySQL.date_fmt)
    
    conn = MySQLdb.connect(host=__HOST, user=__USER, passwd=__PASSWD, unix_socket='/var/run/mysqld/mysqld.sock')
    #with conn as cur:
    if 1:
        # Deletes the existing table.
        cur = conn.cursor()
        query = "DROP TABLE IF exists {}.{};".format(__DB, table_name)
        execute(cur, query)

        # Creates a new table.
        query = "CREATE TABLE {}.{} (".format(__DB, table_name)

        query += "id INT UNSIGNED NOT NULL PRIMARY KEY, "
        query += "date DATETIME, "
        query += "header_keyword VARCHAR(255) NOT NULL, "
        query += "header_value_type VARCHAR(255) NOT NULL, "
        query += "header_value VARCHAR(255) DEFAULT 'TBW', "
        query += "header_value_format VARCHAR(255), "
        query += "header_value_unit VARCHAR(255), "
        query += "header_comment VARCHAR(255) NOT NULL, "
        query += "obe_mode VARCHAR(255) DEFAULT 'common', "
        query += "fetch_timing VARCHAR(255) NOT NULL, "
        query += "updater VARCHAR(255) NOT NULL, "
        query += "inst_table_name VARCHAR(255), "
        query += "inst_table_column_name VARCHAR(255), "
        query += "ide_header_keyword VARCHAR(255), "
        query += "ocs_param_name VARCHAR(255), "
        query += "python_method VARCHAR(255)"
#        query += "comment VARCHAR(255)"

        query += " ) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;"

        execute(cur, query)

        # Adds data.
        for line in data:
            vals = collections.OrderedDict()

            vals["id"] = line[0]
            vals["date"] = dt  #line[1]
            vals["header_keyword"] = line[2]
            vals["header_value_type"] = line[3]
            vals["header_value"] = "##NODATA##"  #line[4]
            vals["header_value_format"] = line[5]
            vals["header_value_unit"] = line[6]
            vals["header_comment"] = line[7]
            vals["obe_mode"] = line[8]
            vals["update_timing"] = line[9]
            vals["updater"] = line[10]
            vals["inst_table_name"] = line[11]
            vals["inst_table_column_name"] = line[12]
            vals["ide_header_keyword"] = line[13]
            vals["ocs_param_name"] = line[14]
            vals["python_method"] = line[15]
#            vals["comment"] = line[13]

            query = "INSERT INTO {}.{}".format(__DB, table_name)
            query += " VALUES('"
            query += "', '".join(vals.values())
            query += "')"

            execute(cur, query)

    conn.close()
    print("Done.", file=os.sys.stderr)

    return


def main(infile, delimiter="\t"):
    data = read_file(infile, delimiter)

    table_name = os.path.splitext(os.path.basename(infile))[0]

    create_table(table_name, data)
    create_table(table_name.replace("_master", ""), data)

    return


##########################################################################
if __name__ == "__main__":
    import os
    main(os.sys.argv[1])

