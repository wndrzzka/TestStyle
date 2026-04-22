from typing import Optional, Union

import pyrogram
from pyrogram import enums, raw, types
from ..object import Object

class InlineKeyboardButton(Object):
    def __init__(
        self,
        text: str,
        icon_custom_emoji_id: Optional[str] = None,
        style: Optional["enums.ButtonStyle"] = enums.ButtonStyle.DEFAULT,
        *,
        url: Optional[str] = None,
        user_id: Optional[int] = None,
        callback_data: Optional[Union[str, bytes]] = None,
        web_app: Optional["types.WebAppInfo"] = None,
        login_url: Optional["types.LoginUrl"] = None,
        switch_inline_query: Optional[str] = None,
        switch_inline_query_current_chat: Optional[str] = None,
        switch_inline_query_chosen_chat: Optional["types.SwitchInlineQueryChosenChat"] = None,
        copy_text: Optional["types.CopyTextButton"] = None,
        callback_game: Optional["types.CallbackGame"] = None,
        pay: Optional[bool] = None,
        callback_data_with_password: Optional[bytes] = None,
    ):
        super().__init__()

        self.text = str(text)
        self.icon_custom_emoji_id = icon_custom_emoji_id
        self.style = style
        self.callback_data = callback_data
        self.url = url
        self.web_app = web_app
        self.login_url = login_url
        self.user_id = user_id
        self.switch_inline_query = switch_inline_query
        self.switch_inline_query_current_chat = switch_inline_query_current_chat
        self.switch_inline_query_chosen_chat = switch_inline_query_chosen_chat
        self.callback_game = callback_game
        self.pay = pay
        self.copy_text = copy_text
        self.callback_data_with_password = callback_data_with_password

    @staticmethod
    def read(b: "raw.base.KeyboardButton"):
        raw_style = getattr(b, "style", None)
        button_style = enums.ButtonStyle.DEFAULT
        icon_custom_emoji_id = None
        
        if raw_style is not None:
            if getattr(raw_style, "bg_primary", False):
                button_style = enums.ButtonStyle.PRIMARY
            elif getattr(raw_style, "bg_danger", False):
                button_style = enums.ButtonStyle.DANGER
            elif getattr(raw_style, "bg_success", False):
                button_style = enums.ButtonStyle.SUCCESS
            if getattr(raw_style, "icon", None):
                icon_custom_emoji_id = str(raw_style.icon)

        if isinstance(b, raw.types.KeyboardButtonCallback):
            try:
                data = b.data.decode()
            except UnicodeDecodeError:
                data = b.data

            if getattr(b, "requires_password", None):
                return InlineKeyboardButton(
                    text=b.text,
                    callback_data_with_password=data,
                    style=button_style,
                    icon_custom_emoji_id=icon_custom_emoji_id
                )

            return InlineKeyboardButton(
                text=b.text,
                callback_data=data,
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )

        if isinstance(b, raw.types.KeyboardButtonUrl):
            return InlineKeyboardButton(
                text=b.text,
                url=b.url,
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )

        if isinstance(b, raw.types.KeyboardButtonUrlAuth):
            return InlineKeyboardButton(
                text=b.text,
                login_url=types.LoginUrl.read(b),
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )

        if isinstance(b, raw.types.KeyboardButtonUserProfile):
            return InlineKeyboardButton(
                text=b.text,
                user_id=b.user_id,
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )

        if isinstance(b, raw.types.KeyboardButtonSwitchInline):
            if getattr(b, "same_peer", False):
                return InlineKeyboardButton(
                    text=b.text,
                    switch_inline_query_current_chat=b.query,
                    style=button_style,
                    icon_custom_emoji_id=icon_custom_emoji_id
                )
            elif getattr(b, "peer_types", None):
                return InlineKeyboardButton(
                    text=b.text,
                    switch_inline_query_chosen_chat=types.SwitchInlineQueryChosenChat.read(b),
                    style=button_style,
                    icon_custom_emoji_id=icon_custom_emoji_id
                )
            else:
                return InlineKeyboardButton(
                    text=b.text,
                    switch_inline_query=b.query,
                    style=button_style,
                    icon_custom_emoji_id=icon_custom_emoji_id
                )

        if isinstance(b, raw.types.KeyboardButtonGame):
            return InlineKeyboardButton(
                text=b.text,
                callback_game=types.CallbackGame(),
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )

        if isinstance(b, raw.types.KeyboardButtonWebView):
            return InlineKeyboardButton(
                text=b.text,
                web_app=types.WebAppInfo(url=b.url),
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )
        
        if isinstance(b, raw.types.KeyboardButtonBuy):
            return InlineKeyboardButton(
                text=b.text,
                pay=True,
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )

        if isinstance(b, raw.types.KeyboardButtonCopy):
            return InlineKeyboardButton(
                text=b.text,
                copy_text=types.CopyTextButton(text=b.copy_text),
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )

        if isinstance(b, raw.types.KeyboardButton):
            return InlineKeyboardButton(
                text=b.text,
                style=button_style,
                icon_custom_emoji_id=icon_custom_emoji_id
            )

    async def write(self, client: "pyrogram.Client"):
        raw_style = raw.types.KeyboardButtonStyle(
            bg_primary=self.style == enums.ButtonStyle.PRIMARY,
            bg_danger=self.style == enums.ButtonStyle.DANGER,
            bg_success=self.style == enums.ButtonStyle.SUCCESS,
            icon=int(self.icon_custom_emoji_id) if self.icon_custom_emoji_id else None
        )

        if self.callback_data_with_password is not None:
            if isinstance(self.callback_data_with_password, str):
                raise ValueError("This is not supported")
            return raw.types.KeyboardButtonCallback(
                text=self.text,
                data=self.callback_data_with_password,
                requires_password=True,
                style=raw_style
            )

        if self.callback_data is not None:
            data = bytes(self.callback_data, "utf-8") if isinstance(self.callback_data, str) else self.callback_data
            return raw.types.KeyboardButtonCallback(
                text=self.text,
                data=data,
                style=raw_style
            )

        if self.url is not None:
            return raw.types.KeyboardButtonUrl(
                text=self.text,
                url=self.url,
                style=raw_style
            )

        if self.login_url is not None:
            return self.login_url.write(
                text=self.text,
                bot=await client.resolve_peer(self.login_url.bot_username or "self"),
                style=raw_style
            )

        if self.user_id is not None:
            return raw.types.InputKeyboardButtonUserProfile(
                text=self.text,
                user_id=await client.resolve_peer(self.user_id),
                style=raw_style
            )

        if self.switch_inline_query is not None:
            return raw.types.KeyboardButtonSwitchInline(
                text=self.text,
                query=self.switch_inline_query,
                style=raw_style
            )

        if self.switch_inline_query_current_chat is not None:
            return raw.types.KeyboardButtonSwitchInline(
                text=self.text,
                query=self.switch_inline_query_current_chat,
                same_peer=True,
                style=raw_style
            )

        if self.switch_inline_query_chosen_chat is not None:
            return self.switch_inline_query_chosen_chat.write(
                text=self.text,
                style=raw_style
            )

        if self.callback_game is not None:
            return raw.types.KeyboardButtonGame(
                text=self.text,
                style=raw_style
            )

        if self.web_app is not None:
            return raw.types.KeyboardButtonWebView(
                text=self.text,
                url=self.web_app.url,
                style=raw_style
            )

        if self.pay is not None and self.pay:
            return raw.types.KeyboardButtonBuy(
                text=self.text,
                style=raw_style
            )

        if self.copy_text is not None:
            return raw.types.KeyboardButtonCopy(
                text=self.text,
                copy_text=self.copy_text.text,
                style=raw_style
            )
