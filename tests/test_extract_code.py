import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import types

# Provide stub modules so importing bot does not require heavy dependencies.
sys.modules.setdefault("matplotlib", types.ModuleType("matplotlib"))
sys.modules.setdefault("matplotlib.pyplot", types.ModuleType("matplotlib.pyplot"))

pandas_module = types.ModuleType("pandas")
class DummyDataFrame:
    pass
pandas_module.DataFrame = DummyDataFrame
sys.modules.setdefault("pandas", pandas_module)
telegram_module = types.ModuleType("telegram")
class Update:
    pass
telegram_module.Update = Update
sys.modules.setdefault("telegram", telegram_module)

telegram_ext = types.ModuleType("telegram.ext")
telegram_ext.Application = object
telegram_ext.CommandHandler = object
telegram_ext.MessageHandler = object
telegram_ext.filters = types.SimpleNamespace(TEXT=None, COMMAND=None, Document=None, ALL=None)
telegram_ext.ContextTypes = types.SimpleNamespace(DEFAULT_TYPE=None)
sys.modules.setdefault("telegram.ext", telegram_ext)
openai_module = types.ModuleType("openai")

class DummyAsyncOpenAI:
    def __init__(self, *args, **kwargs):
        pass

openai_module.AsyncOpenAI = DummyAsyncOpenAI
sys.modules.setdefault("openai", openai_module)

os.environ.setdefault("OPENROUTER_API_KEY", "dummy")

import bot


def test_extract_code_basic():
    text = "```python\nprint('hi')\n```"
    assert bot.extract_code(text) == "print('hi')"


def test_extract_code_no_fence():
    text = "print('hi')"
    assert bot.extract_code(text) == "print('hi')"


def test_extract_code_other_text():
    text = "Answer:\n```python\nprint('hi')\n```\nThanks"
    assert bot.extract_code(text) == "print('hi')"
