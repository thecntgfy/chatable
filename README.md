# Chatable Telegram Bot

This repository contains a simple Telegram bot that lets users chat with their data tables.

1. Users upload a `.csv` or `.xlsx` file to the bot.
2. They ask questions about the data in natural language.
3. The bot sends the request along with a summary of the table to the OpenRouter API using the `openai/gpt-4.1-mini` model. The model returns Python code that answers the question.
4. The returned code is executed and the resulting text and/or plot is sent back to the user.

## Running

Set the following environment variables:

- `TELEGRAM_TOKEN` – Telegram bot token.
- `OPENROUTER_API_KEY` – API key for [openrouter.ai](https://openrouter.ai/).

Install dependencies and start the bot:

```bash
pip install -r requirements.txt
python bot.py
```
