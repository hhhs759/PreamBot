import discord
from discord.ext import commands, tasks
import time
import os
from dotenv import load_dotenv

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

flask_thread = Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()



load_dotenv()


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


BANNED_WORDS_FILE = "banned_words.txt"
GOOD_WORDS_FILE = "good_words.txt"


user_last_messages = {}  # {user_id: {'last_message': '', 'count': 0, 'time': 0}}
user_blocks = {}
spam_cooldown = 10
max_repeats = 3
block_duration = 30


bot_messages = []
current_message_index = 0
TARGET_CHANNEL_ID = 1411072853809561650  


def load_banned_words():
    banned_words = []
    if os.path.exists(BANNED_WORDS_FILE):
        try:
            with open(BANNED_WORDS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:
                        banned_words.append(word)
            print(f"Loaded {len(banned_words)} banned words")
        except Exception as e:
            print(f"Error loading banned words: {e}")
    return banned_words

# Load good words for auto messages
def load_good_words():
    good_words = []
    if os.path.exists(GOOD_WORDS_FILE):
        try:
            with open(GOOD_WORDS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    message = line.strip()
                    if message:
                        good_words.append(message)
            print(f"Loaded {len(good_words)} auto messages")
        except Exception as e:
            print(f"Error loading auto messages: {e}")
    return good_words


@tasks.loop(hours=1)
async def send_auto_message():
    global current_message_index, bot_messages

    if not bot_messages:
        return

    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if channel:
        # Check if it's a text channel that supports sending messages
        if hasattr(channel, 'send'):
            try:
                await channel.send(bot_messages[current_message_index])
                print(f"Sent auto message: {bot_messages[current_message_index]}")
                current_message_index = (current_message_index + 1) % len(bot_messages)
            except Exception as e:
                print(f"Error sending auto message: {e}")
        else:
            print(f"Channel {TARGET_CHANNEL_ID} does not support sending messages (may be a forum channel)")

@bot.event
async def on_ready():
    print(f'{bot.user} is now running!')
    bot.banned_words = load_banned_words()

    global bot_messages
    bot_messages = load_good_words()

    if bot_messages:
        send_auto_message.start()
        print("Auto message task started")
    else:
        print("No auto messages to send")


def check_repeat_spam(user_id, message_content):
    current_time = time.time()


    if user_id in user_blocks:
        if current_time < user_blocks[user_id]:
            return "blocked"
        else:
            del user_blocks[user_id]


    if user_id not in user_last_messages:
        user_last_messages[user_id] = {
            'last_message': message_content,
            'count': 1,
            'time': current_time
        }
        return "ok"

    user_data = user_last_messages[user_id]


    if current_time - user_data['time'] > spam_cooldown:
        user_last_messages[user_id] = {
            'last_message': message_content,
            'count': 1,
            'time': current_time
        }
        return "ok"


    if user_data['last_message'] == message_content:
        user_data['count'] += 1
        user_data['time'] = current_time


        if user_data['count'] >= max_repeats:
            user_blocks[user_id] = current_time + block_duration
            return "spam_detected"
    else:

        user_last_messages[user_id] = {
            'last_message': message_content,
            'count': 1,
            'time': current_time
        }

    return "ok"

@bot.event
async def on_message(message):

    if message.author == bot.user or message.author.bot:
        await bot.process_commands(message)
        return

    user_id = message.author.id
    message_content = message.content


    spam_result = check_repeat_spam(user_id, message_content)

    if spam_result == "blocked":
        remaining = int(user_blocks[user_id] - time.time())
        await message.delete()
        await message.channel.send(
            f"⏳ {message.author.mention} Blocked for {remaining} seconds due to spamming!",
            delete_after=5
        )
        return

    elif spam_result == "spam_detected":
        await message.delete()
        await message.channel.send(
            f" {message.author.mention} Blocked for {block_duration} seconds for repeating messages!",
            delete_after=5
        )
        return


    content_lower = message_content.lower()
    if hasattr(bot, 'banned_words'):
        for word in bot.banned_words:
            if word.lower() in content_lower:
                await message.delete()
                await message.channel.send(
                    f" {message.author.mention} This word is not allowed!",
                    delete_after=5
                )
                return


    await bot.process_commands(message)


@bot.command()
@commands.has_permissions(administrator=True)
async def set_repeat(ctx, repeats: int = 3, cooldown: int = 10, duration: int = 30):
    global max_repeats, spam_cooldown, block_duration
    max_repeats = repeats
    spam_cooldown = cooldown
    block_duration = duration
    await ctx.send(f" Settings updated: {repeats} repeats every {cooldown} seconds - block duration: {duration} seconds")


@bot.command()
async def get_settings(ctx):
    await ctx.send(f" Current Settings:\n• Max repeats: {max_repeats}\n• Cooldown: {spam_cooldown} seconds\n• Block duration: {block_duration} seconds")


@bot.command()
@commands.has_permissions(administrator=True)
async def unblock(ctx, member: discord.Member):
    if member.id in user_blocks:
        del user_blocks[member.id]
        if member.id in user_last_messages:
            del user_last_messages[member.id]
        await ctx.send(f" Unblocked {member.mention}")
    else:
        await ctx.send(f" {member.mention} is not blocked")

@bot.command()
@commands.has_permissions(administrator=True)
async def add_message(ctx, *, message: str):
    global bot_messages


    with open(GOOD_WORDS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")


    bot_messages = load_good_words()
    await ctx.send(f" Added auto message: {message}")


@bot.command()
async def list_messages(ctx):
    if not bot_messages:
        await ctx.send(" No auto messages configured")
        return

    messages_list = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(bot_messages)])
    await ctx.send(f" Auto Messages:\n{messages_list}")


token = os.getenv('DISCORD_TOKEN')
if token is None:
    raise ValueError("DISCORD_TOKEN environment variable not set!")
bot.run(token)