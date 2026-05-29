# -*- coding: utf-8 -*-
"""
Created on Wed Feb 18 15:06:07 2026

@author: User
"""

import mysql.connector

connection = mysql.connector.connect(
    host='192.168.0.240',
    user='wifiuser',
    password='HugoChouLePoney!',
    database='maxyver_test',
    port=3307,
    auth_plugin='mysql_native_password'
)
if connection.is_connected():
    db_info = connection.get_server_info()
    print("Connected to MySQL Server version ", db_info)