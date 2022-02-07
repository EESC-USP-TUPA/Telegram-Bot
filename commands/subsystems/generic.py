from telegram.ext import CallbackContext, ConversationHandler
from telegram import ReplyKeyboardRemove, Update
from commands.general import send_keyboard_message

# A dictionary to store information about each conversation, identified by the sender's telegram ID
conversation_task = {}


# Returns standardized string to begin conversation stage
def get_default_system_message(mode: str, description: str) -> str:
    return (
        f"<b>{mode}</b>\n"
        f"{description}\n\n"
        "Utilize <code>/cancel</code> a qualquer momento para cancelar a operação\n"
        "<u>Informe o sistema</u>"
    )


# Function executed whenever a timeout occours
def timeout(update: Update, ctx: CallbackContext) -> int:
    send_keyboard_message(update, "Limite de tempo excedido\nInicie o processo novamente")
    return ConversationHandler.END


# Function executed whenever a conversation is cancelled
def cancel(update: Update, ctx: CallbackContext) -> int:
    send_keyboard_message(update, "Processo cancelado")
    return ConversationHandler.END
