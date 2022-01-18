import commands.subsystems.task_register as task_register
import commands.subsystems.task_list as task_list
from telegram.ext import CallbackContext
from telegram import Update


def query_handler(update: Update, ctx: CallbackContext) -> None:
    query = update.callback_query.data
    [cmd, *args] = query.split(" ")

    if cmd == "list":
        task_list.task_lister(update, ctx, args)

    elif cmd == "add":
        task_register.add_task(update, ctx)
