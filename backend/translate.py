from googletrans import Translator
from tkinter import messagebox as msg


class TranslateText:
    def __init__(self, **kwargs):
        self.translator = Translator()

    def translate_text(self, text, from_lang, to_lang):
        try:
            self.output = self.translator.translate(text, to_lang, from_lang)
            return self.output.text

        except Exception as e:
            print(e)
            print(from_lang, to_lang)
            msg.showerror("No Network", "Unable to translate due to poor internet connection.")

    def auto_detectText(self, text):
        try:
            self.resp = self.translator.detect(text)
            return self.resp.lang

        except Exception as e:
            print(e)
            