import tkinter as tk 
from tkinter import filedialog
import os 
from pygame import mixer
import getpass

path = ""
mixn = mixer.init()
pathx = f"C:\\Users\\{getpass.getuser()}\\Desktop\\LANGUAGE_TRANSLATOR_AUDIOS"#\\2024-07-28"
path_list = []
dir_list = []

def display_folder_content(dir_path,listbox):
    listbox.delete(0,tk.END)
    try:
        folder_contents = path_list[::-1]#os.listdir(folder_path)
        listbox.delete(0,tk.END)

        for item in folder_contents:
            listbox.insert(tk.END,f"\n{path_list.index(item)}  >{item}")
    
    except Exception as e:
        print(e)
        listbox.delete(0,tk.END)
        listbox.insert(tk.END,f"Error {e}")

def open_folder_dialog(path_to_dir,listbox):
    global path
    listbox.delete(0,tk.END)

    path = path_to_dir
    for dirpath, dirnames, filenames in os.walk(path_to_dir):
        for file in filenames:
            if file:
                f = str(file)
                path_list.append(f)
                dir_list.append(dirpath + "\\")
        
                display_folder_content(f,listbox)
            
            else:
                pass



def play_selected(listbox,selected_box):
    for i in listbox.curselection():
        selection = str(listbox.get(i)).split(">")[1]
        x = dir_list[path_list.index(selection)] + "\\" + selection#listbox.get(i)
        try:
            selected_box.delete(0,tk.END)
            selected_box.insert(tk.END,str(x))
            sound = mixer.Sound(x)
            sound.play()
        except:
            print("Cannot play selected file")

def delete_selected(listbox):
    for i in listbox.curselection():
        selection = str(listbox.get(i)).split(">")[1]
        x = dir_list[path_list.index(selection)] + "\\" + selection
        try:
            os.remove(x)
            listbox.delete(0,tk.END)
            display_folder_content(i,listbox)
        
        except Exception as e:
            print(e)
            print("Cannot Delete selected file")

def load_audios(listbox):
    open_folder_dialog(pathx,listbox)
