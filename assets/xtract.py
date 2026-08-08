from .languages_image import bin_data
from .languages_icon import bin_data as bd
from tkinter import messagebox
import getpass
import os

path1 = f"C:\\Users\\{getpass.getuser()}\\Pictures\\languages.png"
path2 = f"C:\\Users\\{getpass.getuser()}\\Pictures\\languages.ico"

class ExtractImages:
    def xtract_images(self):
        try:
            with open(path1,'wb') as f:
                x = f.write(bin_data)
                f.close()

            with open(path2,'wb') as f:
                x = f.write(bd)
                f.close()
        
        except Exception as e:
            messagebox.showerror("Failed Extraction","Failed to extract assets required to run the application")
    
    def delete_images(self):
        os.remove(path1)
        os.remove(path2)
