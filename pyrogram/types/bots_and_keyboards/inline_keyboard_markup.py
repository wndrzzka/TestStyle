#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-present Dan <https://github.com/delivrance>
#
#  This file is part of Pyrogram.
#  Pyrogram is free software: you can redistribute it and/or modify...

from typing import List
import pyrogram
from pyrogram import raw, types
from ..object import Object

class InlineKeyboardMarkup(Object):
    """An inline keyboard that appears right next to the message it belongs to.

    Parameters:
        inline_keyboard (List of List of :obj:`~pyrogram.types.InlineKeyboardButton`):
            List of button rows, each represented by a List of InlineKeyboardButton objects.
    """

    def __init__(self, inline_keyboard: List[List["types.InlineKeyboardButton"]]):
        super().__init__()
        self.inline_keyboard = inline_keyboard

    @staticmethod
    def read(o):
        inline_keyboard = []
        for i in o.rows:
            row = []
            for j in i.buttons:
                row.append(types.InlineKeyboardButton.read(j))
            inline_keyboard.append(row)

        return InlineKeyboardMarkup(
            inline_keyboard=inline_keyboard
        )

    async def write(self, client: "pyrogram.Client"):
        rows = []
        for r in self.inline_keyboard:
            buttons = []
            for b in r:
                buttons.append(await b.write(client))
            rows.append(raw.types.KeyboardButtonRow(buttons=buttons))

        return raw.types.ReplyInlineMarkup(rows=rows)
