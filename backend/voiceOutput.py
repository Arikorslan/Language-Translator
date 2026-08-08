import gtts
# import playsound
import random
from string import digits
import os
from datetime import date
import getpass
import datetime
from pygame import mixer
# import datetime




class  TextToSpeech:
    def __init__(self,**kwargs):
        self.mixer = mixer.init()
        self.user = getpass.getuser()
        self._path = f"C:\\Users\\{self.user}\\Desktop\\LANGUAGE_TRANSLATOR_AUDIOS\\{date.today()}\\"
        try:
            os.makedirs(self._path)
            
        except Exception as e:pass

    def say_text(self,text,lang):#

        _id = ''.join(random.choice(digits) for x in range(6))
        self.filename = f"file_{lang}_{_id}"
        self._tts = gtts.gTTS(text,lang=lang)

        self.path = self._path+self.filename+'.mp3'
        self._tts.save(f"{self.path}")

        sound = mixer.Sound(self.path)
        sound.play()
        os.remove(self.path)
       
    
    def say_Savetext(self,text,lang,fullLang):
        _id = ''.join(random.choice(digits) for x in range(6))
        self.filename = f"file_{fullLang}_{_id}"
        self._tts = gtts.gTTS(text,lang=lang)
        self.path = f"{self._path}{self.filename}.mp3"
        saved = self._tts.save(f"{self.path}")
        print(self.path,"iam here")
        
        return self.path

       