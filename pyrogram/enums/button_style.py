from enum import auto
from .auto_name import AutoName

class ButtonStyle(AutoName):
    """Button style type enumeration used in :obj:`~pyrogram.types.KeyboardButton` and :obj:`~pyrogram.types.InlineKeyboardButton` to describe the style of a button."""

    DEFAULT = auto()
    "The button has default style"

    PRIMARY = auto()
    "The button has dark blue color"

    DANGER = auto()
    "The button has red color"

    SUCCESS = auto()
    "The button has green color"
