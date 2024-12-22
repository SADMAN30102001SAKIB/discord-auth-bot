import asyncio
import os
import sys

import discord
import requests
from discord.ext import commands

TOKEN = os.getenv(
    "DISCORD_TOKEN",
    "MTI5NDAxNjE4MDE5NzEzMDI1MQ.GB93Tg.wTqieZt3A3BvSMxP6cNr5O7LVsNXRzslBaVGQM",
)
API_KEY = os.getenv("API_KEY", "TapSs@14023010.com")
FLASK_SERVER_URL = "https://sadmansakib.pythonanywhere.com"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

ROLE_NAME = "Subscriber"


def get_tokens():
    try:
        response = requests.get(
            f"{FLASK_SERVER_URL}/showtokens", params={"api_key": API_KEY}
        )
        response.raise_for_status()
        return set(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tokens: {e}")
        return set()


def save_tokens(tokens):
    try:
        response = requests.post(
            f"{FLASK_SERVER_URL}/savetokens",
            json={"tokens": list(tokens)},
        )
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error saving tokens: {e}")
        return False


def log_user(username, token):
    data = {"username": username, "token": token}
    try:
        response = requests.post(f"{FLASK_SERVER_URL}/loguser", json=data)
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error logging user: {e}")
        return False


@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name == "verify":
        submitted_token = message.content.strip()
        if len(submitted_token) != 10:
            await message.channel.send(
                f"❌ Invalid token. Token must be exactly 10 characters long {message.author.mention}."
            )

            try:
                await message.delete()
            except discord.Forbidden:
                print("Bot doesn't have permission to delete messages.")
            except discord.HTTPException:
                print("Failed to delete message due to an HTTP error.")

            return

        role_names_to_check = ["Admin", "Mod", "Bot", ROLE_NAME]
        for role_name in role_names_to_check:
            role = discord.utils.get(message.guild.roles, name=role_name)
            if role and role in message.author.roles:
                if role_name == ROLE_NAME:
                    await message.channel.send(
                        f"⚠️ {message.author.mention}, you are already a Subscriber."
                    )
                else:
                    await message.channel.send(
                        f"⚠️ {message.author.mention}, you are already in a privileged role."
                    )
                return

        tokens_cache = get_tokens()
        if submitted_token in tokens_cache:
            role = discord.utils.get(message.guild.roles, name=ROLE_NAME)
            if role:
                flag1 = False
                flag2 = False
                tokens_cache.discard(submitted_token)
                flag1 = save_tokens(tokens_cache)
                if flag1:
                    flag2 = log_user(str(message.author), submitted_token)

                if flag2:
                    await message.author.add_roles(role)
                    await message.channel.send(
                        f"✅ {message.author.mention}, you have been verified and assigned the Subscriber role!"
                    )
                else:
                    await message.channel.send(
                        f"❌ An error occurred while verifying your token. Please try again {message.author.mention}."
                    )
            else:
                await message.channel.send(
                    f'❌ Role "{ROLE_NAME}" not found. Please contact an admin {message.author.mention}.'
                )
        else:
            await message.channel.send(
                f"❌ Invalid token. Please check your token and try again {message.author.mention}!"
            )

        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    await bot.process_commands(message)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

if __name__ == "__main__":
    asyncio.run(bot.start(TOKEN))
