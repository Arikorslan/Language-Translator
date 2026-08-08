import pyttsx3
import getpass
import random
phrases = [f"Hi {getpass.getuser()}, iam listening.",'iam listening','go on',"lets hear what you have to say",'iam all ears',"go ahead and tell me","waiting for you","ready when your ready","tunyu ke","ready when your ready!"]

class offline:
    def speak(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate',140)
        self.engine.say(''.join(random.choice(phrases)))
        self.engine.runAndWait()

