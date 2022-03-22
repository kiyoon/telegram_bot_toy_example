#!/usr/bin/env python3
import coloredlogs, logging
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from configparser import ConfigParser
import os
import traceback

import json

logger = logging.getLogger(__name__)

__SCRIPT_DIR__ = os.path.dirname(os.path.realpath(__file__))

class ListBot:
    def __init__(self, token, filter_chat_ids):
        self.updater = Updater(token, use_context=True)
        self.dp = self.updater.dispatcher
        self.filter_chat_ids = filter_chat_ids
        self.list_of_data = ['Initial data 1', 'Initial data 2']

    
    def run(self):
        self.dp.add_handler(CommandHandler('start', self.start, filters=Filters.user(self.filter_chat_ids)))
        self.dp.add_handler(CommandHandler('help', self.help, filters=Filters.user(self.filter_chat_ids)))
        self.dp.add_handler(CommandHandler('list', self.list, filters=Filters.user(self.filter_chat_ids)))
        self.dp.add_handler(CommandHandler('del', self.delete, pass_args = True, filters=Filters.user(self.filter_chat_ids)))
        self.dp.add_handler(CallbackQueryHandler(self.button))
        self.dp.add_handler(MessageHandler(Filters.text & Filters.user(self.filter_chat_ids),
                                           self.message))
        self.dp.add_error_handler(self.error)
        self.updater.start_polling()
        logger.info('Listening...')
        self.updater.idle()


    def start(self, update, context):
        self.help(update, context)


    def help(self, update, context):
        #context.bot.send_message(chat_id=update.message.chat_id, text="")
        #context.bot.send_message(chat_id=update.effective_chat.id, text="")
        update.message.reply_text("*Simple list bot*\n"
                                  "Available commands:\n\n"
                                  "/help\n"
                                  "Show this help\n\n"
                                  "/list\n"
                                  "List all items\n\n"
                                  "/del id\n"
                                  "Delete item at index `id`\n\n"
                                  "Send any message without / prefix to append a string to the list.\n\n"
                                  )


    def list(self, update, context):
        if len(self.list_of_data) == 0:
            update.message.reply_text("No items in the list.")
        else:
            for idx, item in enumerate(self.list_of_data):
                update.message.reply_text(f"{idx}: {item}")

    
    def delete(self, update, context):
        if len(self.list_of_data) == 0:
            update.message.reply_text("No item in the list")
        else:
            if len(context.args) == 0:
                update.message.reply_text('No arguments. You need to specify the index of the list.')
                return
            elif len(context.args) > 1:
                update.message.reply_text('Too many arguments. You need to specify the index of the list.')
                return


            delete_idx = int(context.args[0])
            assert delete_idx >= 0
            assert delete_idx < len(self.list_of_data)

            button_options = ['Yes', 'No']
            button_list = []
            for option in button_options:
                # Be careful not to exceed 64-byte limit for the callback_data.
                callback_data = json.dumps({'command': 'del', 'option': option, 'idx': delete_idx}, separators = (",", ":"))
                button_list.append(InlineKeyboardButton(option, callback_data = callback_data))
            reply_markup = InlineKeyboardMarkup(self._build_menu(button_list, n_cols = 2))  # n_cols = 1 is for single column and mutliple rows
            update.message.reply_text(f"<b>Are you sure you want to remove this?</b>\n\n{self.list_of_data[delete_idx]}", parse_mode='html', reply_markup=reply_markup)


    def button(self, update, context):
        query = update.callback_query
        data = json.loads(query.data)
        if data['command'] == 'del':
            if data['option'] == 'Yes':
                del self.list_of_data[data['idx']]
                msg = "Successfully removed from the list!"
            else:
                msg = "Operation cancelled."
            
            query.edit_message_text(text=query.message.text_html + f"\n\n<b>Selected option: {data['option']}</b>\n\n{msg}", parse_mode='html')
        else:
            raise NotImplementedError("Unable to recognise the command using the inline keyboard button.")


    def _build_menu(self, buttons,n_cols,header_buttons=None,footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        if header_buttons:
            menu.insert(0, header_buttons)
        if footer_buttons:
            menu.append(footer_buttons)
        return menu


    def message(self, update, context):
        string_to_append = update.message.text
        update.message.reply_text(f"'{string_to_append}' added to the list at index {len(self.list_of_data)}")
        self.list_of_data.append(string_to_append)


    def error(self, update, context):
        logger.error('Update "%s" caused error "%s"' % (update, context.error))
        traceback.print_exc(context.error)

if __name__ == "__main__":
    coloredlogs.install(fmt='%(asctime)s - %(name)s: %(lineno)4d - %(levelname)s - %(message)s', level='DEBUG')

    config = ConfigParser()
    config.read(os.path.join(__SCRIPT_DIR__, "key.ini"))
    token = config['Telegram']['token']
    filter_chat_ids = list(map(int, config['Telegram']['filter_chat_ids'].split(",")))

    bot = ListBot(token, filter_chat_ids)
    bot.run()

