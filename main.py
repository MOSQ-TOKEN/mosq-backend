from fastapi import Request
from fastapi.responses import JSONResponse
import asyncio, uvicorn
import os, telebot
from database import MongoDB
from keys import *
# Telebot settings
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
from telebot.async_telebot import AsyncTeleBot
telebot.apihelper.SESSION_TIME_TO_LIVE = None
from telebot import asyncio_filters

# Bot Instance
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = AsyncTeleBot(token=BOT_TOKEN, state_storage=StateMemoryStorage())

# Server Config
from fastapi_app import app

server_url = os.getenv("server_url")


@bot.message_handler(commands=['start'])
async def referral_command(msg):
    try:
        chat_id = msg.chat.id

        if msg.chat.type != 'private':
            return

        await bot.send_message(
            chat_id=chat_id,
            text=f"welcome to mosqui bobo",
            reply_markup=welcome_keyboard(),
            parse_mode="Markdown"
        )

        who_referred = await extract_unique_code(msg.text)
        # print(msg.from_user)
        is_premium = msg.from_user.is_premium

        username = msg.from_user.username or msg.from_user.firstname
        # confirm if start comes from user not in database ..t.me/mosqebot/start_2383884
        if who_referred is not None:
            async with MongoDB() as db:
                await db.save_new_user(uid=chat_id, is_premium=is_premium, invitor=int(who_referred))
        elif who_referred is None:
            async with MongoDB() as db:
                await db.save_new_user(username, is_premium, 1896706785)
    except Exception as a:
        print("referral_command err:", a)


async def extract_unique_code(text):
    try:
        # Extracts the unique_code from the sent /start command.
        return text.split()[1] if len(text.split()) > 1 else None
    except Exception as b:
        print("extract_unique_code err:", b)

# Add custom filters
bot.add_custom_filter(asyncio_filters.StateFilter(bot))

@app.post('/add_task')
async def add_task(request: Request):
    try:
        data = await request.json()
        task_name = data.get('task_name')
        task_point = data.get('task_point')
        task_link = data.get('task_link')
        if task_name:
            # increment userid point
            async with MongoDB() as db:
                result = await db.add_task(task_name, task_point, task_link)
            return JSONResponse({"data": f"{result}"},status_code=200)
        else:
            return JSONResponse({"data": "no user_id in sent data"}, status_code=200)
    except Exception as x:
        print("add_task webhook error:", x)
        return JSONResponse({"error": str(x)}, status_code=504)
    
@app.post('/task_complete')
async def task_complete(request: Request):
    try:
        data = await request.json()
        # EXPECT: userid, chat_id 
        # CHANGE: alocate 
        user_id = data.get('user_id')
        task_name = data.get('task_name')
        if user_id:
            # increment userid point
            async with MongoDB() as db:
                await db.task_complete(user_id, task_name)
            return JSONResponse({"data": "point increased"},status_code=200)
        else:
            return JSONResponse({"data": "no user_id in sent data"}, status_code=200)
    except Exception as x:
        print("addtoken webhook error:", x)
        return JSONResponse({"error": str(x)}, status_code=504)
    
@app.post('/check_in')
async def check_in(request: Request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        if user_id :
            async with MongoDB() as db:
                result = await db.check_in(user_id)
            return JSONResponse({"data": result} ,status_code=200)
        else:
            return JSONResponse({"data": "user not found!"}, status_code=200)
    except Exception as x:
        print("check_in webhook error:", x)
        return JSONResponse({"error": str(x)}, status_code=504)
    
@app.get('/user_data')
async def user_data(request: Request):
    try:
        data = await request.json()
        # EXPECT: userid, chat_id 
        # CHANGE: alocate 
        user_id = data.get('user_id')
        if user_id :
            async with MongoDB() as db:
                result = await db.user_data(user_id)
            return JSONResponse({"data": result} ,status_code=200)
        else:
            return JSONResponse({"data": "user not found!"}, status_code=200)
    except Exception as x:
        print("addtoken webhook error:", x)
        return JSONResponse({"error": str(x)}, status_code=504)
    
@app.get('/get_all_users')
async def get_all_users(request: Request):
    try:
        async with MongoDB() as db:
            result = await db.get_all_users()
        return JSONResponse({"data": f"{result}"} ,status_code=200)
    except Exception as x:
        print("get_all_users webhook error:", x)
        return JSONResponse({"error": str(x)}, status_code=504)
    
@app.post('/end_game')
async def end_game(request: Request):
    try:
        data = await request.json()
        # EXPECT: userid, chat_id 
        # CHANGE: alocate 
        user_id = data.get('user_id')
        game_points = data.get('game_points')
        if user_id :
            async with MongoDB() as db:
                result = await db.end_game(user_id, game_points)
            return JSONResponse({"data": "point increased"},status_code=200)
        else:
            return JSONResponse({"data": "no user_id in sent data"}, status_code=200)
    except Exception as x:
        print("addtoken webhook error:", x)
        return JSONResponse({"error": str(x)}, status_code=504)
    
    
@app.post('/' + BOT_TOKEN)
async def getMessage(update: dict):
    update = telebot.types.Update.de_json(update)
    await bot.process_new_updates([update])
    return "", 200

@app.route("/")
async def webhook():
    await bot.remove_webhook()
    await bot.set_webhook(url=f'{server_url}/' + BOT_TOKEN)
    return "", 200

async def main():
    config = uvicorn.Config("fastapi_app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def couple():
    try:
        print("coupling")
        await asyncio.gather(webhook(), main())
    except Exception as x:
        print("couple err:", x)

if __name__ == '__main__':
    asyncio.run(couple())
