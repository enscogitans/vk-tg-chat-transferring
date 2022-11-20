from datetime import datetime

import tg_importer.types as tg
from vk_tg_converter.contacts.username_manager import ContactInfo


class DummyHistoryProvider:
    @staticmethod
    def make_history(contacts: list[ContactInfo]) -> tg.ChatHistory:
        ts = datetime.now()
        tg_messages: list[tg.Message] = []
        for contact in contacts:
            user = contact.tg_name_opt or contact.vk_name
            text = f"vk: {contact.vk_name}\ntg: {contact.tg_name_opt}"
            tg_messages.append(tg.Message(ts=ts, user=user, text=text))
        return tg.ChatHistory(messages=tg_messages, title_opt="Chat title", photo_opt=None)
