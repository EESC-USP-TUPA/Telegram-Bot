# TODO
# Fix document adding bug
# Add comment option
# Add project name and merging
# Export similar functions to other module
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
from telegram.ext import (
    MessageHandler,
    Filters,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
)
from gspread import Worksheet
from datetime import date
from unidecode import unidecode
from commands.general import log_command
from spreadsheet import Spreadsheet, systems
from commands.general import create_keyboard, send_keyboard_message
from commands.subsystems.generic import get_default_system_message, timeout, cancel

"""
Task Creation file
Creates a conversation with user to prompt for new task info
When finished, the new task is inserted directly in Google Spreadsheet
"""

# States of conversation
[
    SYSTEM,
    SUBSYSTEM,
    PROJECT,
    TASK,
    DIFFICULTY,
    DURATION,
    DOC_QUESTION,
    DOCUMENTS,
    NOTES,
    CONFIRMATION,
] = range(10)


# New task info
task_info = {
    "system": str,
    "subsystem": str,
    "project": str,
    "new_project": bool,
    "task": str,
    "diff": str,
    "duration": str,
    "docs": str,
    "notes": str,
}

# New task env info
new_task = {"ss": Spreadsheet, "dict": dict, "task": task_info, "proj": list}


def add_task(update: Update, ctx: CallbackContext) -> int:
    log_command("register")
    description = "Adiciona uma nova tarefa na planilha de atividades do subsistema"
    text = get_default_system_message("Adicionar tarefa", description)
    send_keyboard_message(update, text, create_keyboard([["ele", "mec"]]))
    return SYSTEM


def system(update: Update, ctx: CallbackContext) -> int:
    system = update.message.text
    if system == "ele":
        subsystems = [["bt", "pt"], ["hw", "sw"]]
    elif system == "mec":
        subsystems = [["ch"]]

    else:
        send_keyboard_message(text="Sistema não encontrado")
        return ConversationHandler.END

    global new_task
    keyboard = create_keyboard(subsystems)

    new_task["task"]["system"] = system
    new_task["dict"] = systems[system]["sub"]
    new_task["ss"] = systems[system]["ss"]

    send_keyboard_message(update, "Informe o subsistema", keyboard)
    return SUBSYSTEM


def get_active_projects() -> str:
    global new_task
    ss = new_task["ss"].sheet(new_task["task"]["subsystem"])
    data = ss.get_all_values()
    projects = [f"{index+1} - {row[0]}" for index, row in enumerate(row for row in data if row[0])]

    new_task["proj"] = projects
    return "\n".join(projects)


def subsystem(update: Update, ctx: CallbackContext) -> int:
    subsystem = update.message.text
    global new_task
    new_task["task"]["subsystem"] = subsystem
    reply_text = (
        f"<b>Subsistema: {new_task['dict'][subsystem]['name']}</b>\n\n"
        "Para adicionar a tarefa a um projeto existente, forneça seu número\n"
        "Para adicionar um novo projeto, insira o nome deste "
        "(capitalização e acentuação são importantes)\n\n"
        f"<u>Projetos Ativos</u>\n{get_active_projects()}"
    )

    update.message.reply_text(reply_text, reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)
    return PROJECT


def project(update: Update, ctx: CallbackContext) -> int:
    project = update.message.text
    global new_task

    try:
        project_number = int(project)
        new_task["task"]["new_project"] = False
        new_task["task"]["project"] = new_task["proj"][project_number - 1].split(" - ")[1]

    except:
        new_task["task"]["project"] = project
        new_task["task"]["new_project"] = True

    update.message.reply_text(
        f"Projeto {new_task['task']['project']} selecionado\n"
        "Insira o nome da tarefa\n"
        "Capitalização e acentuação são importantes",
    )
    return TASK


def task(update: Update, ctx: CallbackContext) -> int:
    global new_task
    new_task["task"]["task"] = update.message.text
    update.message.reply_text("Forneça uma estimativa (0 - 10) para a dificuldade desta tarefa")
    return DIFFICULTY


def difficulty(update: Update, ctx: CallbackContext) -> int:
    try:
        difficulty = float(update.message.text)
        if difficulty < 0 or difficulty > 10:
            raise Exception

    except:
        update.message.reply_text("Entrada inválida!\n\nA dificuldade deve ser um número entre 1 e 10")
        return DIFFICULTY

    global new_task
    new_task["task"]["diff"] = difficulty
    update.message.reply_text("Forneça uma estimativa de tempo (em semanas) para a realização desta tarefa")
    return DURATION


def duration(update: Update, ctx: CallbackContext) -> int:
    try:
        dur = float(update.message.text)
        if dur < 0:
            raise Exception
    except:
        update.message.reply_text("Entrada inválida!\n\nForneça um número positivo")
        return DURATION

    global new_task
    new_task["task"]["duration"] = dur
    question = [["Sim", "Não"]]
    update.message.reply_text(
        "Gostaria de associar esta tarefa a algum documento?",
        reply_markup=ReplyKeyboardMarkup(question, one_time_keyboard=True),
    )
    return DOC_QUESTION


def documents_question(update: Update, ctx: CallbackContext) -> int:
    answer = unidecode(update.message.text.lower())
    if answer == "sim":
        update.message.reply_text("Forneça o link para o(s) documento(s)", reply_markup=ReplyKeyboardRemove())
        return DOCUMENTS


def documents(update: Update, ctx: CallbackContext) -> int:
    global new_task
    new_task["task"]["docs"] = update.message.text if unidecode(update.message.text.lower()) != "nao" else ""

    question = [["Sim", "Não"]]
    update.message.reply_text(
        "<b>Confirme as informações</b>\n\n"
        f"<i>Subsistema:</i> {new_task['dict'][new_task['task']['subsystem']]['name']}\n"
        f"<i>Projeto:</i> {new_task['task']['project']}\n"
        f"<i>Tarefa:</i> {new_task['task']['task']}\n"
        f"<i>Dificuldade:</i> {new_task['task']['diff']}\n"
        f"<i>Duração:</i> {new_task['task']['duration']}\n\n"
        "Deseja adicionar a tarefa?",
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardMarkup(question, one_time_keyboard=True),
    )
    return CONFIRMATION


def find_project_index(proj, data) -> int:
    for index, p in enumerate(data):
        if p[0] == proj:
            return index + 1
    return -1


def add_task_to_sheet() -> None:
    global new_task
    ss: Worksheet = new_task["ss"].sheet(new_task["task"]["subsystem"])
    data = ss.get_all_values()
    if new_task["task"]["new_project"]:
        index = len(data) + 1
    else:
        index = find_project_index(new_task["task"]["project"], data)
        while not data[index][0]:
            index += 1
        index += 1
        ss.insert_row([], index=index)

    task = new_task["task"]
    ss.update(
        f"A{index}:J{index}",
        [
            [
                task["project"],
                task["task"],
                "A fazer",
                date.today().strftime("%d/%m/%Y"),
                task["duration"],
                task["diff"],
                "",
                "",
                "",
                task["docs"],
            ]
        ],
    )


def confirmation(update: Update, ctx: CallbackContext) -> int:
    answer = unidecode(update.message.text.lower())
    if answer == "sim":
        add_task_to_sheet()
        update.message.reply_text("Tarefa adicionada com sucesso", reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text("Processo cancelado", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


register_handler = ConversationHandler(
    entry_points=[CommandHandler("add", add_task)],
    states={
        SYSTEM: [MessageHandler(Filters.text & ~Filters.command, system)],
        SUBSYSTEM: [MessageHandler(Filters.text & ~Filters.command, subsystem)],
        PROJECT: [MessageHandler(Filters.text & ~Filters.command, project)],
        TASK: [MessageHandler(Filters.text & ~Filters.command, task)],
        DIFFICULTY: [MessageHandler(Filters.text & ~Filters.command, difficulty)],
        DURATION: [MessageHandler(Filters.text & ~Filters.command, duration)],
        DOC_QUESTION: [MessageHandler(Filters.text & ~Filters.command, documents_question)],
        DOCUMENTS: [MessageHandler(Filters.text & ~Filters.command, documents)],
        CONFIRMATION: [MessageHandler(Filters.text & ~Filters.command, confirmation)],
        ConversationHandler.TIMEOUT: [MessageHandler(Filters.text | Filters.command, timeout)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    conversation_timeout=30,
)
