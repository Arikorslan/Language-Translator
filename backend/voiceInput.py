import speech_recognition as sr 
from .offline_speech import offline
#pip install googletrans --user
from tkinter import messagebox as msg



class RecogniseAudio:
    def __init__(self,**kwargs):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone(1)

    def listenToAudio(self):
        Audiodata = ""
        try:
            # offline().speak()
            with sr.Microphone() as self.source:
                self.recognizer.adjust_for_ambient_noise(self.source,1)
                said = self.recognizer.listen(self.source)
                Audiodata = self.recognizer.recognize_google(audio_data=said)
                print(f"You said {Audiodata}")
            
            return Audiodata
        
        except Exception as e:
            print(e)
            msg.showerror("Something's wrong", "Something went wrong while processing your input.")


            
        