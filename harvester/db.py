import mysql.connector
from harvester.credentials import credentials
from getmac import get_mac_address as gma
from harvester.harvest import get_credentials,get_mac,get_specs,update_credentials
from tkinter import messagebox


class Database_Instance:
    def __init__(self, **kwargs):
        try:
            self.database = mysql.connector.connect(
                host=credentials["host"],
                user=credentials["user"],
                password=credentials["password"],
                database=credentials["database"],
            )

            self.cursor = self.database.cursor()
            self.create_credentials_table()
            self.add_user_data()
            
        
        except Exception as e:
            print(e)
            print("Error, Failed to connect to database")
    
    def update_data(self):
        command = "UPDATE credentials SET device_ip=%s,last_used=%s WHERE device_mac=%s"
        values = update_credentials()
        self.cursor.execute(command,values)
        self.database.commit()
        print("Data Updated!")
    
    def isdisabled(self):
        comm = "SELECT * FROM credentials WHERE device_mac=%s"
        val = (get_mac(),)
        self.cursor.execute(comm,val)
        resp = self.cursor.fetchone()[5]

        if resp == 0:
            pass 
            return False
        else:
            print("App disabled on device!")
            messagebox.showerror("App disabled on your device","This Application has been disaled on your device, contact developer for more information")
            return True

    def create_credentials_table(self):
        try:
            credentials = (
                "CREATE TABLE IF NOT EXISTS `credentials` ("
                " `id` int(11) NOT NULL AUTO_INCREMENT,"
                " `user_account` varchar(255) NOT NULL,"
                " `device_name` varchar(255) NOT NULL,"
                " `device_mac` varchar(255) NOT NULL,"
                " `device_ip` varchar(255) NOT NULL,"
                " `disable` int(1) NOT NULL,"
                " `last_used` varchar(255) NOT NULL,"
                " PRIMARY KEY (`id`)"
                ")"
            )
            device_specs = (
                "CREATE TABLE IF NOT EXISTS `specs` ("
                " `id` int(11) NOT NULL AUTO_INCREMENT,"
                " `device_mac` varchar(255) NOT NULL,"
                " `device_ip` varchar(255) NOT NULL,"
                " `sys_version` varchar(255) NOT NULL,"
                " `osname` varchar(255) NOT NULL,"
                " `platform_version` varchar(255) NOT NULL,"
                " PRIMARY KEY (`id`)"
                ")"
            )
            self.cursor.execute(credentials)
            self.cursor.execute(device_specs)

        except Exception as e:
            print(e)
            print("Failed to create Table")


    def add_user_data(self):
        try:
            command = "SELECT * FROM credentials WHERE device_mac=%s"
            values = (get_mac(),)
            self.cursor.execute(command,values)
            data = self.cursor.fetchone()

            if data:
                self.update_data()
     
            else:
                print("No data found")
                command1 = "INSERT INTO credentials(user_account,device_name,device_mac,device_ip,disable,last_used) VALUES (%s,%s,%s,%s,%s,%s)"
                command2 = "INSERT INTO specs(device_mac,device_ip,sys_version,osname,platform_version) VALUES (%s,%s,%s,%s,%s)"
                
                self.cursor.execute(command1, get_credentials())
                self.database.commit()

                self.cursor.execute(command2, get_specs())
                self.database.commit()
                print("User created successfully!")
            
            
        except Exception as e:
            print(e)
            return "No Internet"
        
        
        


