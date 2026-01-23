# discord_bot.py
import asyncio
import traceback

import discord
from discord.ext import commands

from src.adapters.retrieval import QdrantCodeRetriever
from src.adapters.llm import GrokCompleter
from src.application.application import get_initial_history, process_conversation_turn
from src.utils import split_into_messages

from src.config import (
    DISCORD_COMMAND_PREFIX,
    MESSAGE_CHUNK_LIMIT,
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=DISCORD_COMMAND_PREFIX, intents=intents, help_command=None)

histories: dict[int, list[dict]] = {}

code_retriever = QdrantCodeRetriever()
llm_completer = GrokCompleter()


@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready to answer Hytale modding questions!")


@bot.command(name="hy", aliases=["askhy"])
async def hy_command(ctx: commands.Context, *, query: str = None):
    if query is None or not query.strip():
        await ctx.send(
            "Please ask a question about the Hytale server codebase after the command!\n"
            "Example: `!hy How does the weather system work?`"
        )
        return

    user_id = ctx.author.id

    if user_id not in histories:
        histories[user_id] = get_initial_history()

    current_history = histories[user_id]

    thinking_msg = await ctx.send("Processing...")

    try:
        async with ctx.typing():
            response, new_history, trimmed = await asyncio.to_thread(
                process_conversation_turn,
                current_history,
                query,
                code_retriever,
                llm_completer,
            )
    except Exception:
        await thinking_msg.edit(content="Sorry, something went wrong.")
        traceback.print_exc()
        return

    histories[user_id] = new_history

    chunks = split_into_messages(response, limit=MESSAGE_CHUNK_LIMIT)

    if len(chunks) == 1:
        await thinking_msg.edit(content=chunks[0])
    else:
        await thinking_msg.edit(content=chunks[0])
        for chunk in chunks[1:]:
            await ctx.send(chunk)

    if trimmed:
        await ctx.send("Conversation history was trimmed to prevent token overflow.")


@bot.command(name="clear")
async def clear_history(ctx: commands.Context):
    user_id = ctx.author.id
    if user_id in histories:
        del histories[user_id]
    await ctx.send("Your conversation history has been cleared!")
