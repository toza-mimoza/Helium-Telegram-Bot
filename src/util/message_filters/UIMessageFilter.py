from telegram import Update, Message
from telegram.ext.filters import MessageFilter
from util import UiLabels

class UIMessageFilter(MessageFilter):
    __slots__ = ()
    def filter(self, message: Message):
        acceptable_list = [
            UiLabels.UI_LABEL_MAIN_MENU,
            UiLabels.UI_LABEL_MENU_BACK,
            UiLabels.UI_LABEL_MENU_SETTINGS,
            # UiLabels.UI_LABEL_MENU_SETUP,
            UiLabels.UI_LABEL_MENU_START,
            UiLabels.UI_LABEL_MENU_STOP,
            UiLabels.UI_LABEL_MENU_SNOOZE]

        if message.text in acceptable_list:
            return True
        return False

UI = UIMessageFilter(name='filters.UI')