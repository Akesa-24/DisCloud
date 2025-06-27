import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import io


load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}!")

@bot.event
async def on_member_join(member):
    await member.send(f"Hello, {member.name}!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "shit" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} dont use that word!")

    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.mention}!")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name="Gamer")
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} You are now assigned to {role}!")
    else:
        await ctx.send(f"{ctx.author.mention} You are not assigned to any role!")

@bot.command()
async def list_txt(ctx):
    txt_files = []
    async for msg in ctx.channel.history(limit=200):
        for attachment in msg.attachments:
            if attachment.filename.endswith('.txt'):
                txt_files.append(attachment.filename)

    if txt_files:
        await ctx.send("Found .txt files:\n" + "\n".join(txt_files))
    else:
        await ctx.send("No .txt files found.")

@bot.command()
async def search_txt(ctx):
    async for message in ctx.channel.history(limit=100):  # Search last 100 messages
        for attachment in message.attachments:
            if attachment.filename.endswith('.txt'):
                await ctx.send(f"Found .txt file: {attachment.filename}")


@bot.command()
async def read_txt(ctx):
    async for message in ctx.channel.history(limit=100):
        for attachment in message.attachments:
            if attachment.filename.endswith('.txt'):
                file_bytes = await attachment.read()  # Read file as bytes
                content = file_bytes.decode('utf-8')  # Decode to string
                await ctx.send(f"Contents of {attachment.filename}:\n{content[:1900]}")  # Trim to avoid 2000 char limit




@bot.command()
async def generate_and_send(ctx, content = "This is a generated text file.\nLine 2\nLine 3"): # THIS WILL NOT BE USED BECAUSE WE DONT SEND FROM THE SERVER, BUT IT IS PROOF OF CONCEPT

    # Create cool in-memory file, but not in storage
    file = io.StringIO(content)

    byte_file = io.BytesIO(file.getvalue().encode("utf-8"))
    byte_file.seek(0)

    await ctx.send("Generated file:", file=discord.File(byte_file, filename="generated.txt"))


bot.run(token, log_handler=handler, log_level=logging.DEBUG)