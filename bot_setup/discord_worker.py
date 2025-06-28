from fileinput import filename

import discord
from discord.ext import tasks, commands
import json
import io
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
QUEUE_PATH = "C:\\Users\\Lenovo\\Documents\\GitHub\\DisCloud\\shared\\task_queue.json"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    channel = bot.get_channel(691580400501260332)
    await channel.send(f"{bot.user.name} is online!")
    task_watcher.start()

@tasks.loop(seconds=5)  # checks every 5 seconds
async def task_watcher():
    print("Task Watcher loop")
    if not os.path.exists(QUEUE_PATH):
        print("Queue file does not exist")
        return

    with open(QUEUE_PATH, "r+", encoding="utf-8") as f:
        print("in Queue path")
        try:
            tasks_list = json.load(f)
            print(tasks_list)
        except json.JSONDecodeError:
            print("Corrupt queue, skipping.")
            return

        remaining_tasks = []

        for task in tasks_list:
            print(task["task"])
            if task["task"] == "send":
                await handle_send(task)
            elif task["task"] == "read":
                await handle_read(task)
            elif task["task"] == "delete":
                pass #TODO

            else:
                print("Unknown task:", task)
                remaining_tasks.append(task)

        # Clear processed tasks
        f.seek(0)
        f.truncate()
        json.dump(remaining_tasks, f, indent=2)

async def handle_send(task):
    print('Handling sending')
    channel = bot.get_channel(task["channel_id"])
    if not channel:
        print("Channel not found")
        return

    content = task["content"]
    filename = task.get("filename", "message.txt")

    temp_file = io.BytesIO(content.encode("utf-8"))
    print('Sending')
    await channel.send(file=discord.File(temp_file, filename=filename))

async def handle_read(task):
    channel = bot.get_channel(task["channel_id"])
    if not channel:
        print("Channel not found")
        return

    async for msg in channel.history(limit=50):
        for attachment in msg.attachments:
            if attachment.filename.endswith(".txt"):
                data = await attachment.read()
                content = data.decode("utf-8")
                # write output to file
                with open(f"C:\\Users\\Lenovo\\Documents\\GitHub\\DisCloud\\read\\{attachment.filename}", "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"C:\\Users\\Lenovo\\Documents\\GitHub\\DisCloud\\read\\{attachment.filename}")
                return

bot.run(TOKEN)
