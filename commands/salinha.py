
from telegram import Update
from telegram.ext import CallbackContext
import tkinter
import playsound
import threading

from .general import reply_text
from .help import get_default_description


# Command called when a new person starts a conversation with the bot
def salinha(update: Update, ctx: CallbackContext) -> None:
    root = tkinter.Tk()
    root.geometry("700x500")

    canvas = tkinter.Canvas(root, width=700, height=500, bg="white")

    canvas.create_text(350, 230, text="ABRIR PORTA", fill="black", font=('Helvetica 30 bold'))
    canvas.pack()
    threading.Thread(target=playsound.playsound, args=('sound.mp3',), daemon=True).start()
    root.mainloop()
    
    start_text = (
        "Olá, eu sou o <b>Tupão</b>, o bot do Tupã.\n"
        "Fui desenvolvido com o intuito de automatizar alguns processos e "
        "facilitar a vida das pessoas.\n\n"
        "Atualmente conto com alguns comandos, listados abaixo."
    )
    reply_text(update, f"{start_text}\n\n{get_default_description()}")
