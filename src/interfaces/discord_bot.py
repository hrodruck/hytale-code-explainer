# discord_bot.py
import asyncio
import time
import traceback

import discord
from discord.ext import commands

from src.adapters.retrieval import QdrantCodeRetriever
from src.adapters.llm import get_llm_completer
from src.application.application import get_initial_history, process_conversation_turn
from src.utils import split_into_messages, log_usage_metric, anonymize_user_id

from src.config import (
    DISCORD_COMMAND_PREFIX,
    MESSAGE_CHUNK_LIMIT,
    METRICS_FILE,
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=DISCORD_COMMAND_PREFIX, intents=intents, help_command=None)

histories: dict[int, list[dict]] = {}

code_retriever = QdrantCodeRetriever()
llm_completer = get_llm_completer()

@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready to answer Hytale modding questions!")
    log_usage_metric("bot_startup", {"bot_user": str(bot.user)}, filename=METRICS_FILE)


@bot.command(name="hy", aliases=["askhy"])
async def hy_command(ctx: commands.Context, *, query: str = None):
    user_id = ctx.author.id
    user_id_str = anonymize_user_id(str(user_id))

    start_time = time.time()

    if query is None or not query.strip():
        await ctx.send(
            "Please ask a question about the Hytale server codebase after the command!\n"
            "Example: `!hy How does the weather system work?`"
        )
        duration = time.time() - start_time
        log_usage_metric("command_invocation", {
            "command": "hy",
            "user_id": user_id_str,
            "success": False,
            "duration_seconds": round(duration, 3),
            "reason": "empty_query",
        }, filename=METRICS_FILE)
        return

    query_stripped = query.strip()
    query_length = len(query_stripped)

    # Initialize history if this is a new user session
    new_conversation = False
    if user_id not in histories:
        histories[user_id] = get_initial_history()
        new_conversation = True
        log_usage_metric("new_conversation", {"user_id": user_id_str}, filename=METRICS_FILE)

    current_history = histories[user_id]

    thinking_msg = await ctx.send("Processing...")

    success = False
    response_chunks = 0
    history_trimmed = False
    error_reason = None

    try:
        async with ctx.typing():
            response, new_history, trimmed = await asyncio.to_thread(
                process_conversation_turn,
                current_history,
                query_stripped,
                code_retriever,
                llm_completer,
            )

        # Success path
        histories[user_id] = new_history
        history_trimmed = trimmed

        chunks = split_into_messages(response, limit=MESSAGE_CHUNK_LIMIT)
        response_chunks = len(chunks)

        if response_chunks == 1:
            await thinking_msg.edit(content=chunks[0])
        else:
            await thinking_msg.edit(content=chunks[0])
            for chunk in chunks[1:]:
                await ctx.send(chunk)

        if trimmed:
            await ctx.send("Conversation history was trimmed to prevent token overflow.")

        success = True

    except Exception as exc:
        error_reason = type(exc).__name__
        await thinking_msg.edit(content="Sorry, something went wrong. Please wait and try again.")
        traceback.print_exc()

    finally:
        duration = time.time() - start_time

        metric_details = {
            "command": "hy",
            "user_id": user_id_str,
            "success": success,
            "duration_seconds": round(duration, 3),
            "query_char_count": query_length,
            "new_conversation": new_conversation,
        }

        if success:
            metric_details.update({
                "response_chunks": response_chunks,
                "history_trimmed": history_trimmed,
            })
        else:
            metric_details["error_reason"] = error_reason

        log_usage_metric("command_invocation", metric_details, filename=METRICS_FILE)


@bot.command(name="clear")
async def clear_history(ctx: commands.Context):
    user_id = ctx.author.id
    user_id_str = str(user_id)

    start_time = time.time()

    history_existed = user_id in histories
    if history_existed:
        del histories[user_id]

    await ctx.send("Your conversation history has been cleared!")

    duration = time.time() - start_time

    log_usage_metric("command_invocation", {
        "command": "clear",
        "user_id": user_id_str,
        "success": True,
        "duration_seconds": round(duration, 3),
        "history_existed_before_clear": history_existed,
    }, filename=METRICS_FILE)