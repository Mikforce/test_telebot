import asyncio
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pyrogram import Client, filters
from datetime import datetime, timedelta

Base = declarative_base()

# Определение модели данных для пользователей
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime)
    status = Column(String)
    status_updated_at = Column(DateTime)

# Определение модели данных для сообщений
class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime)
    text = Column(String)
    checkpoint = Column(String)
    cancellation_trigger = Column(String)
    status_updated_at = Column(DateTime)

engine_users = create_engine('sqlite:///users.db', echo=True)
Base.metadata.create_all(engine_users)
SessionUsers = sessionmaker(bind=engine_users)

engine_messages = create_engine('sqlite:///messages.db', echo=True)
Base.metadata.create_all(engine_messages)
SessionMessages = sessionmaker(bind=engine_messages)

api_id = '21384363'
api_hash = '6a6571ca440248fe322c2eb9cf3df03e'
bot_token = '6560868723:AAFltN3ADO9L7kBnA3eahdB7dgmpo6QuE9Q'

app = Client("testtelebot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)


# async def process_message(user, message):
#     session_users = SessionUsers()
#     lowercase_message = message.text
#     if not user:
#         user = User(id=message.from_user.id, created_at=message.date, status='alive')
#         session_users.add(user)
#
#     if user.status == 'dead' or user.status == 'finished':
#         session_users.close()
#         return
#
#     if 'прекрасно' in lowercase_message or 'ожидать' in lowercase_message:
#         user.status = 'finished'
#         user.status_updated_at = message.date
#         session_users.commit()
#         session_users.close()
#         return
#
#     if 'триггер1' in lowercase_message:
#         user.status = 'finished'
#         user.status_updated_at = message.date
#         session_users.commit()
#         session_users.close()
#         return
#     print(message)
#     with SessionMessages() as session:
#         new_message = Message(time=message.date, text=message.text, checkpoint=None, cancellation_trigger=None,
#                               status_updated_at=None)
#         session.add(new_message)
#         session.commit()
#         session_users.close()
#         await message.reply_text("Сообщение успешно обработано и сохранено в базе данных! 🚀")
async def process_message(user, message):
    session_users = SessionUsers()
    stop_words = ["прекрасно", "ожидать"]
    print(message)
    lowercase_message = message.text.lower()

    if not user:
        user = User(id=message.from_user.id, created_at=message.date, status='alive')
        session_users.add(user)

    if user.status == 'dead' or user.status == 'finished':
        session_users.close()
        return

    if any(word in lowercase_message for word in stop_words):
        user.status = 'finished'
        user.status_updated_at = message.date
        session_users.commit()
        session_users.close()
        return

    if 'триггер1' in lowercase_message:
        user.status = 'finished'
        user.status_updated_at = message.date
        session_users.commit()
        session_users.close()
        return

    with SessionMessages() as session:
        if user.status == 'alive' or user.status == 'sent_msg_1':
            new_message = Message(
                time=datetime.fromtimestamp((message.date - user.created_at).total_seconds() // 60),
                text=message.text,
                checkpoint="Первое сообщение клиента",
                cancellation_trigger="msg_1",
                status_updated_at=None
            )
            user.status = 'sent_msg_1'
        elif user.status == 'sent_msg_1':
            new_message = Message(
                time=datetime.fromtimestamp((message.date - user.created_at).total_seconds() // 60),
                text=message.text,
                checkpoint="Время отправки сообщения msg_1",
                cancellation_trigger="Триггер1",
                status_updated_at=None
            )
            user.status = 'sent_msg_2'
        elif user.status == 'sent_msg_2':
            new_message = Message(
                time=datetime.fromtimestamp((message.date - user.created_at).total_seconds() // 3600),
                text=message.text,
                checkpoint="Время отправки сообщения msg_2 или время, когда оно было отменено (найден триггер)",
                cancellation_trigger="msg_3",
                status_updated_at=None
            )
            user.status = 'finished'

        session.add(new_message)
        session.commit()
        await message.reply_text("Сообщение успешно обработано и сохранено в базе данных! 🚀")

    session_users.commit()
    session_users.close()


@app.on_message(filters.private)
async def message_handler(client, message):
    if message.text:
        session_users = SessionUsers()
        user = session_users.query(User).filter_by(id=message.from_user.id).first()
        await process_message(user, message)




        session_users.close()

if __name__ == '__main__':
    app.run()