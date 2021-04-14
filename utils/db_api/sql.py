import sqlite3
from aiogram import types
from check_db import path_to_db


class DBCommands:
    path = path_to_db
    CHECK_OAUTH_USER = "SELECT oauth_token, oauth_token_secret FROM users WHERE my_id=?"
    ADD_NEW_USER = 'INSERT INTO users (my_id, first_name, second_name, oauth_token, oauth_token_secret) values(?, ?, ?, ?, ?)'
    

    async def check_user(self):
        command = self.CHECK_OAUTH_USER
        user = types.User.get_current()
        my_id = int(user.id)
        result = None
        try:
            conn = sqlite3.connect(self.path)
            result = conn.execute(command, (my_id,)).fetchall()
        except:
            print('Возникла ошибка в check_user')
        finally:
            conn.close()
        if result:
            return True
        else:
            return False

    async def oauth(self, oauth_token, oauth_token_secret):
        command = self.ADD_NEW_USER
        user = types.User.get_current()
        my_id = int(user.id)
        first_name = user.first_name
        second_name = user.last_name
        try:
            conn = sqlite3.connect(self.path)
            conn.execute(command, (my_id, first_name, second_name, oauth_token, oauth_token_secret))
            conn.commit()
        except:
            print('Возникла ошибка в reg')
        finally:
            conn.close()
    
    async def access(self):
        command = self.CHECK_OAUTH_USER
        user = types.User.get_current()
        my_id = int(user.id)
        try:
            conn = sqlite3.connect(self.path)
            result = conn.execute(command, (my_id,)).fetchone()
        except:
            print('Возникла ошибка в access')
        finally:
            conn.close()
        if result:
            return result
        else:
            return False