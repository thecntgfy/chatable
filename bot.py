import os
import io
import logging
from contextlib import redirect_stdout

import matplotlib.pyplot as plt
import pandas as pd
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY environment variable is required")

openai.api_key = OPENROUTER_API_KEY
openai.base_url = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-4.1-mini"

# In-memory user storage
user_data = {}

SYSTEM_PROMPT = (
    "You are a helpful data analyst in a Telegram bot. "
    "Users upload CSV or XLSX files. They ask questions about the data. "
    "Generate Python code using pandas (df variable) and matplotlib if needed. "
    "If plotting, save figures to 'output.png'. "
    "Only return the Python code without explanations."
)

def summarize_dataframe(df: pd.DataFrame, max_rows: int = 5) -> str:
    summary = [
        f"shape: {df.shape}",
        f"columns: {list(df.columns)}",
        "dtypes:\n" + df.dtypes.astype(str).to_string(),
        "head:\n" + df.head(max_rows).to_string(),
    ]
    return "\n".join(summary)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Send me a CSV or XLSX file to begin.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    if not document:
        return
    file_name = document.file_name or ""
    if not (file_name.endswith(".csv") or file_name.endswith(".xlsx")):
        await update.message.reply_text("Please upload a CSV or XLSX file.")
        return
    file = await document.get_file()
    file_path = os.path.join(context.application.bot_data.get("tmp", "/tmp"), file_name)
    await file.download_to_drive(file_path)
    if file_name.endswith(".csv"):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path)
    user_data[update.effective_user.id] = {
        "df": df,
        "history": [{"role": "system", "content": SYSTEM_PROMPT}],
    }
    await update.message.reply_text("File loaded. Ask me about your data!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    if uid not in user_data:
        await update.message.reply_text("Please send a CSV or XLSX file first.")
        return
    df = user_data[uid]["df"]
    history = user_data[uid]["history"]

    user_msg = update.message.text
    history.append({"role": "user", "content": user_msg})

    context_info = summarize_dataframe(df)
    messages = history + [{"role": "user", "content": f"Table info:\n{context_info}"}]

    resp = await openai.ChatCompletion.acreate(
        model=MODEL,
        messages=messages,
    )
    code = resp.choices[0].message.content
    history.append({"role": "assistant", "content": code})

    stdout = io.StringIO()
    output_file = "output.png"
    if os.path.exists(output_file):
        os.remove(output_file)
    local_vars = {"df": df, "plt": plt}
    try:
        with redirect_stdout(stdout):
            exec(code, {}, local_vars)
    except Exception as e:
        await update.message.reply_text(f"Error executing code: {e}")
        return
    output_text = stdout.getvalue()
    if output_text:
        await update.message.reply_text(f"\`\`\`\n{output_text}\n\`\`\`", parse_mode="Markdown")
    if os.path.exists(output_file):
        await update.message.reply_photo(photo=open(output_file, "rb"))

async def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN environment variable is required")
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.idle()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
