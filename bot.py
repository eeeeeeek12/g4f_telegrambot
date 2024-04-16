import configparser
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram import F
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import g4f
import json

cfg = configparser.ConfigParser()
cfg.read('config.ini')
API_token = cfg['g']['api']

bot = Bot(token=API_token)
dp = Dispatcher()

# CREATE NEW USER'S CONTEXT FILE (OR CLEAR CONTEXT)
def newcontext(userID):
    with open(f'contexts\\{userID}.json', 'w', encoding="utf-8") as file:
        standart_context = []
        data = json.dumps(standart_context)
        file.write(data)

# GET USER'S CONTEXT
def readcontext(userID):
    try:
        with open(f'contexts\\{userID}.json', encoding="utf-8") as file:
            data = json.load(file)
        return data # list
        
    except Exception as exc:
        newcontext(userID)
        readcontext(userID)

# WRITE NEW MESSAGES TO USER'S CONTEXT
def writecontext(userID, new_prompt, answer_to_new_prompt):
    try:
        with open(f'contexts//{userID}.json', encoding="utf-8") as file:
            data = json.load(file) # list
        
        data.append(new_prompt)
        data.append({'role' : 'assistant', 'content' : answer_to_new_prompt})
        
        with open(f'contexts//{userID}.json', 'w', encoding="utf-8") as file:
            r = json.dumps(data)
            file.write(r)
            
    except Exception as exc:
        newcontext(userID)
        readcontext(userID)

# /start
@dp.message(F.text, Command('start'))
async def start(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🗑 Очистить"))
    builder.add(types.KeyboardButton(text="🅰️ Аккаунт"))
    builder.add(types.KeyboardButton(text="❓ Помощь"))
    builder.adjust(3)

    newcontext(message.from_user.id)

    await message.answer('Привет! Я - бот, который использует GPT модель для общения с тобой. Я могу говорить на разных языках и создавать разные виды контента. Напиши мне что-нибудь, и я постараюсь ответить.', reply_markup=builder.as_markup(resize_keyboard=True))

# /cc
@dp.message(F.text, Command('cc'))
async def cc(message: types.Message):
    newcontext(message.from_user.id)
    await message.answer('🗑 Контекст диалога был сброшен.')

@dp.message(F.text)
async def text_message(message:types.Message):
    if message.text[0] == '/':
        await message.answer('❔ Такой команды не существует.')

    elif message.text == '🗑 Очистить':
        newcontext(message.from_user.id)
        await message.answer('🗑 Контекст диалога был сброшен.')

    elif message.text == '🅰️ Аккаунт':
        await message.answer(f'🅰️ Аккаунт\n\nВ данный момент бот доступен всем асболютно беслпатно и без ограничений!\n\nТвой ID: <code>{message.chat.id}</code>', parse_mode = ParseMode.HTML)

    elif message.text == '❓ Помощь':
        await message.answer(f'''❓ Помощь

Для генерации - просто пришли сообщение с запросом.
Если ассистенту не удалось сгенерировать ответ, попробуй ещё раз, немного изменив свой запрос.

/start
Приветственное сообщение
/cc
Сбросить контекст диалога
    
Создал бота великий и могучий [mksklf](https://t.me/mksklf)''', parse_mode = ParseMode.MARKDOWN, disable_web_page_preview=True)

    else:
        messy = await message.reply('💬 Ожидайте, выполняется генерация ответа...')
    
        try:
            NEW_PROMPT = {"role": "user", "content": message.text}
            
            CONTEXT = readcontext(message.from_user.id)
                
            response = g4f.ChatCompletion.create(
                model=g4f.models.default,
                provider=g4f.Provider.You,
                messages=[
                        *CONTEXT,
                        NEW_PROMPT
                    ],
                stream=False,
                web_search=True
                )
            
            abz = response.split('\n\n')

            abz2 = []
            c = False
            for i in abz:
                if i[:3] == '```':
                    if c:
                        c = False
                    else:
                        c = True
                    abz2.append(i)
                else:
                    if not c:
                        i = i.replace('**', '*')
                        abz2.append(i)
                    else:
                        abz2.append(i)

            response = '\n\n'.join(abz2)

            messy = await bot.edit_message_text(
                text = response,
                chat_id = message.chat.id,
                message_id = messy.message_id,
                disable_web_page_preview=True,
                parse_mode = ParseMode.MARKDOWN
            )

            writecontext(message.from_user.id, NEW_PROMPT, response)
                        
        except Exception as exc:
            print(exc)
            messy = await bot.edit_message_text(
                text = f'❌ Не удалось сгенерировать ответ.',
                chat_id = message.chat.id,
                message_id = messy.message_id,
                parse_mode = ParseMode.MARKDOWN
            )

async def main():
    await dp.start_polling(bot, timeout=200)

if __name__ == '__main__':
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())