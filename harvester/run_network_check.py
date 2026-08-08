import requests 
from harvester.db import Database_Instance
import getpass
import os
import shutil
from tkinter import messagebox

path = f"C:\\Users\\{getpass.getuser()}\\AppData\\Local\\lang\\configuration"#configuration.cfg"

def log_data():
    try:
        if os.path.exists(path):
            with open(path + "\configuration.cfg",'wb+') as f:
                f.write(b'1')
                f.close()
        else:
            os.mkdir(path)
            with open(path + "\configuration.cfg",'wb+') as f:
                f.write(b'1')
                f.close()
        
    except Exception as e:
       print(e)
    
def offline_check(root):
    if (os.path.exists(path)) or (os.path.exists(f"C:\\Users\\{getpass.getuser()}\\AppData\\Local\\lang\\configuration\configuration.cfg")):
        try:
            resp = requests.get('https://www.google.com')
            if resp:
                # os.remove(path + "configuration.cfg")
                os.system(f"rmdir {path} /s /q")
                connected(root)
        except requests.ConnectionError:
            root.destroy()
            messagebox.showwarning("Internet Connection Needed","Application Is temporarily disabled please contact the developer or connect to the internet and restart the app to verify its authenticity")
            # os.remove(__file__)

    
    else:
        run_connection_check(root)
    
def connected(root_window):
    db = Database_Instance()
    if db.isdisabled():
        log_data()
        root_window.destroy()
        return False
    
    else:
        if os.path.exists(path):
            try:
                os.remove(path + "\configuration.cfg")
                os.rmdir(path)
            except:pass

        print("Yay iam connected")
        db.add_user_data()
        return True

def notconnected(root):
    offline_check(root)

def run_connection_check():
    retry = True
    while retry:
        try:
            resp = requests.get("https://www.google.com",timeout=10)
            if resp.status_code == 200:
                retry = False
            return True

            
        except:
            return False

            