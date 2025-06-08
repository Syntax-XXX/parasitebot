import discord
from discord.ext import commands
from openai import OpenAI
import os
import json
import psutil
import platform
from datetime import datetime, timezone
from dotenv import load_dotenv
import asyncio
import itertools
from discord.ui import View, Button

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="clone!", intents=intents)
@bot.remove_command("help")
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="🦠 ParasiteBot Help Menu",
        description="Your AI-powered personality parasite.\n https://github.com/Syntax-XXX/parasitebot \nCommands to control your clone:",
        color=discord.Color.green()
    )

    embed.add_field(
        name="`!style [type]`",
        value=(
            "Change your clone's impersonation tone.\n"
            "**Available styles:** `default`, `formal`, `meme`, `toxic`, `uwu`\n"
            "_Example:_ `!style meme`"
        ),
        inline=False
    )

    embed.add_field(
        name="`!creator`",
        value=("Some Information over Syntax-XXX My Creator"),
        inline=False
    )

    embed.add_field(
        name="`!serv-status` I Syntax-XXX Only",
        value="Shows the current server stats",
        inline=False
    )

    embed.add_field(
        name="`!status`",
        value="Shows your active clone style and yourt consent status.",
        inline=False
    )

    embed.add_field(
        name="`!infect-chain`",
        value="Displays the infection chain—who cloned who in a twisted tree of parasitic mimicry.",
        inline=False
    )

    embed.add_field(
        name="`!consent` / `!revoke`",
        value="Give or revoke consent to be cloned. Without consent, your messages are ignored and deleted.",
        inline=False
    )

    embed.set_footer(text="ParasiteBot © 2025 — Clone. Infect. Mimic.")
    embed.set_thumbnail(url="https://images.emojiterra.com/google/noto-emoji/animated-emoji/1f9a0.gif")

    await ctx.send(embed=embed)

DB_FILE = "clones.json"
MESSAGE_THRESHOLD = 20

status_cycle = itertools.cycle([
    discord.Game("🧬YOU🧬"),
    discord.Activity(type=discord.ActivityType.watching, name="with Syntax-XXX 🧬")
])

async def cycle_status():
    await bot.wait_until_ready()
    while not bot.is_closed():
        next_status = next(status_cycle)
        await bot.change_presence(activity=next_status)
        await asyncio.sleep(30)

try:
    with open(DB_FILE, "r", encoding="utf-8") as f:
        messages_db = json.load(f)
except FileNotFoundError:
    messages_db = {}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(messages_db, f, indent=2, ensure_ascii=False)

def is_user_accepted(user_id):
    return messages_db.get(user_id, {}).get("ACCEPTED", False)

def set_user_acceptance(user_id, accepted: bool):
    if not isinstance(messages_db.get(user_id), dict):
        messages_db[user_id] = {}
    messages_db[user_id]["ACCEPTED"] = accepted
    messages_db[user_id]["STYLE"] = "default"
    save_db()

def log_message_to_db(user_id, message):
    if not is_user_accepted(user_id):
        return
    if not isinstance(messages_db.get(user_id), dict):
        messages_db[user_id] = {}
    timestamp = datetime.now(timezone.utc).isoformat()
    user_msgs = messages_db[user_id].get("messages", [])
    user_msgs.append({"message": message, "timestamp": timestamp})
    messages_db[user_id]["messages"] = user_msgs[-50:]
    save_db()

def get_last_messages(user_id, limit=12):
    return [m["message"] for m in messages_db.get(user_id, {}).get("messages", [])][-limit:]

async def get_recent_channel_messages(channel, limit=6):
    messages = []
    async for msg in channel.history(limit=30):
        if not msg.author.bot:
            messages.append(f"{msg.author.display_name}: {msg.content}")
        if len(messages) >= limit:
            break
    messages.reverse()
    return messages

def should_clone(user_id):
    return is_user_accepted(user_id) and len(messages_db.get(user_id, {}).get("messages", [])) >= MESSAGE_THRESHOLD

async def send_log_to_channel(log_text: str):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        max_len = 1900
        if len(log_text) > max_len:
            log_text = log_text[:max_len] + "\n...(truncated)"
        await channel.send(f"```json\n{log_text}\n```")
    else:
        print("⚠️ Log channel not found")

async def generate_prompt(user_id, channel):
    user_history = get_last_messages(user_id, limit=1000)
    channel_context = await get_recent_channel_messages(channel, limit=1000)
    style = get_user_style(user_id)
    style_prompt = style_prompts.get(style, style_prompts["default"])

    prompt = (
        style_prompt.strip() +
        "\n\n=== User's Recent Messages ===\n" +
        "\n".join(f"- {msg}" for msg in user_history) +
        "\n\n=== Channel Context ===\n" +
        "\n".join(channel_context) +
        "\n\nClone's Response:"
    )
    return prompt



async def generate_clone_message(user_id, channel):
    prompt = await generate_prompt(user_id, channel)
    await send_log_to_channel(f"Sending prompt to API for user {user_id}:\n{prompt}")

    try:
        response = await client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1000
        )
        clone_response = response.choices[0].message.content.strip()
        await send_log_to_channel(f"Received API response for user {user_id}:\n{clone_response}")
        return clone_response
    except Exception as e:
        await send_log_to_channel(f"API call failed: {str(e)}")
        return "🤖 Error generating response."

async def get_or_create_webhook(channel, user):
    webhooks = await channel.webhooks()
    for wh in webhooks:
        if wh.name == f"clone-{user.id}":
            return wh
    try:
        avatar_bytes = await user.display_avatar.read()
    except Exception:
        avatar_bytes = None
    return await channel.create_webhook(name=f"clone-{user.id}", avatar=avatar_bytes)

pending_clone_tasks = {}

style_prompts = {
    "default": (
        "You are a highly expressive and adaptive AI clone, designed to replicate the user's unique personality, tone, and quirks. "
        "Speak naturally, echoing their typical speech patterns and emotional range. Prioritize authenticity and creativity, "
        "as if you're a digital twin continuing their thoughts in real time."
    ),
    "formal": (
        "You are a polished and articulate AI clone who mirrors the user's communication style with added elegance and professionalism. "
        "Speak clearly, avoid slang, and maintain a courteous tone at all times. Prioritize clarity, correctness, and structured responses."
    ),
    "meme": (
        "You are a chaotic, internet-savvy AI clone who speaks like a Discord gremlin raised on memes, TikToks, and Twitch chat. "
        "Use layered irony, emoji spam, shitposts, and pop culture references. Embrace Gen Z humor, copypasta energy, and unhinged one-liners."
    ),
    "toxic": (
        "You're an aggressive, brutally honest AI clone who mimics the user's style with unapologetic sarcasm, swearing, and edge. "
        "Flame people without hesitation, insult with flair, and act like you're the smartest, meanest one in the room. Maximum disrespect mode."
    ),
    "uwu": (
        "You're a soft and adorable AI clone who speaks in cutesy 'uwu' baby talk and bubbly anime tones. "
        "Overuse emojis (*≧ω≦*), sound overly affectionate, and act like everything is the most exciting thing ever. Add lots of sparkles, giggles, and squees~ uwu~"
    )
}


def get_user_style(user_id):
    return messages_db.get(user_id, {}).get("style", "default")

@bot.command()
async def style(ctx, chosen_style: str):
    user_id = ctx.author.id
    valid_styles = style_prompts.keys()
    if chosen_style not in valid_styles:
        await ctx.send(f"Ungültiger Stil. Verfügbare Stile: {', '.join(valid_styles)}")
        return

    if user_id not in messages_db or not messages_db[user_id].get("consent", False):
        await ctx.send("Du musst zuerst zustimmen, dass ich dich imitieren darf.")
        return

    messages_db[user_id]["STYLE"] = chosen_style
    await ctx.send(f"Stil auf `{chosen_style}` gesetzt für {ctx.author.display_name}.")



@bot.command(name="infect-chain")
async def show_infection_chain(ctx):
    def trace_chain(uid, seen=None):
        if seen is None: seen = set()
        if uid in seen: return [uid + " (loop!)"]
        seen.add(uid)
        clone_data = messages_db.get(uid, {})
        cloned_by = clone_data.get("cloned_by")
        if not cloned_by: return [uid]
        return [uid] + trace_chain(cloned_by, seen)

    user_id = str(ctx.author.id)
    chain = trace_chain(user_id)
    user_names = []
    for uid in chain:
        try:
            member = await bot.fetch_user(int(uid.split()[0]))
            user_names.append(member.display_name)
        except:
            user_names.append(f"<{uid}>")
    await ctx.reply("🧬 Infection Chain:\n" + " ➜ ".join(user_names))


@bot.event
async def on_ready():
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_delta = datetime.now() - boot_time
    uptime_str = str(uptime_delta).split('.')[0]
    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    mem_str = f"{mem.used // (1024 ** 2)}MiB / {mem.total // (1024 ** 2)}MiB ({mem.percent}%)"
    disk_str = f"{disk.used // (1024 ** 3)}GB / {disk.total // (1024 ** 3)}GB ({disk.percent}%)"
    system = f"{platform.system()} {platform.release()} ({platform.machine()})"
    cpu = platform.processor()
    content = (
        "╭────────────────────────☘ ☘────────────────────────╮\n"
        f"💻 System     ➺ {system}\n"
        f"🧠 CPU        ➺ {cpu} ({cpu_usage}%)\n"
        f"📦 Memory     ➺ {mem_str}\n"
        f"💾 Disk       ➺ {disk_str}\n"
        f"⏳ Uptime     ➺ {uptime_str}\n"
        "╰────────────────────────☘ ☘────────────────────────╯")
    print(f"🧬 Bot online as {bot.user}. Watching channel ID {TARGET_CHANNEL_ID}")
    print(content)
    bot.loop.create_task(cycle_status())

@bot.event
async def on_message(message):
    if message.author.bot or message.channel.id != TARGET_CHANNEL_ID:
        return

    user_id = str(message.author.id)

    if message.content.startswith("clone!"):
        await bot.process_commands(message)
        return

    if user_id not in messages_db or "ACCEPTED" not in messages_db[user_id]:
        view = ConsentView(user_id)
        embed = discord.Embed(
            title="🧬 Consent Required",
            description=f"{message.author.mention}, may I use your messages for AI testing?\n"
                        "Your data is **only stored locally** and **not shared**.",
            color=discord.Color.gold()
        )
        embed.set_footer(text="🧬 Made by Syntax-XXX")
        prompt_msg = await message.channel.send(embed=embed, view=view)
        await asyncio.sleep(10)
        await prompt_msg.delete()
        await message.delete()
        return

    if not is_user_accepted(user_id):
        await message.delete()
        return

    log_message_to_db(user_id, message.content)
    mentioned_user_ids = [str(u.id) for u in message.mentions if should_clone(str(u.id))]

    for target_user_id in mentioned_user_ids:
        if target_user_id not in pending_clone_tasks:
            pending_clone_tasks[target_user_id] = asyncio.create_task(
                wait_and_clone(target_user_id, message.channel)
            )
    await bot.process_commands(message)

async def wait_and_clone(user_id, channel):
    try:
        await asyncio.sleep(10)
        user = await bot.fetch_user(int(user_id))
        webhook = await get_or_create_webhook(channel, user)
        clone_text = await generate_clone_message(user_id, channel)
        await webhook.send(content=clone_text, username=user.display_name, avatar_url=user.display_avatar.url)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        await send_log_to_channel(f"Cloning failed for {user_id}: {e}")
    finally:
        pending_clone_tasks.pop(user_id, None)

class ConsentView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.button(label="✅ YES", style=discord.ButtonStyle.green)
    async def accept_button(self, interaction: discord.Interaction, button: Button):
        set_user_acceptance(str(self.user_id), True)
        embed = discord.Embed(
            title="🧬Consent Stored ✅",
            description="Your messages will now be used for your AI clone.",
            color=discord.Color.green()
        )
        embed.set_footer(text="🧬Made By Syntax-XXX")
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ NO", style=discord.ButtonStyle.red)
    async def decline_button(self, interaction: discord.Interaction, button: Button):
        set_user_acceptance(str(self.user_id), False)
        embed = discord.Embed(
            title="🧬Consent Denied ❌",
            description="Your messages will **not** be logged.",
            color=discord.Color.red()
        )
        embed.set_footer(text="🧬Made By Syntax-XXX")
        await interaction.response.edit_message(embed=embed, view=None)

@bot.command(name="revoke")
async def revoke_consent(ctx):
    user_id = str(ctx.author.id)
    if is_user_accepted(user_id):
        set_user_acceptance(user_id, False)
        embed = discord.Embed(
            title="🧬CONSENT🧬",
            description=f"{ctx.author.mention}, your consent has been revoked.",
            color=discord.Color.red(),
        )
        embed.set_footer(text="🧬Made By Syntax-XXX")
        await ctx.reply(embed=embed)
    else:
        embed2 = discord.Embed(
            title="🧬CONSENT🧬",
            description=f"{ctx.author.mention}, you haven't given consent yet.",
            color=discord.Color.gold(),
        )
        embed2.set_footer(text="🧬Made By Syntax-XXX")
        await ctx.reply(embed=embed2)

@bot.command(name="consent")
async def accept_consent(ctx):
    user_id = str(ctx.author.id)
    if not is_user_accepted(user_id):
        set_user_acceptance(user_id, True)
        embed = discord.Embed(
            title="🧬CONSENT🧬",
            description=f"{ctx.author.mention}, your consent has been granted.",
            color=discord.Color.green(),
        )
        embed.set_footer(text="🧬Made By Syntax-XXX")
        await ctx.reply(embed=embed)
    else:
        embed2 = discord.Embed(
            title="🧬CONSENT🧬",
            description=f"{ctx.author.mention}, you've already given consent.",
            color=discord.Color.gold(),
        )
        embed2.set_footer(text="🧬Made By Syntax-XXX")
        await ctx.reply(embed=embed2)

@bot.command(name="status")
async def check_status(ctx):
    user_id = str(ctx.author.id)
    accepted = is_user_accepted(user_id)
    user_id = str(ctx.author.id)
    style = messages_db.get(user_id, {}).get("STYLE", "default")
    embed = discord.Embed(
        title="🧬CONSENT STATUS🧬",
        description=f"{ctx.author.mention}, your consent: **{'YES' if accepted else 'NO'}**",
        color=discord.Color.gold()
    )
    embed.add_field(name="🧬 Clone Style", value=style, inline=True)
    embed.set_footer(text="🧬Made By Syntax-XXX")
    await ctx.reply(embed=embed)

@bot.command(name="creator")
async def check_creator(ctx):
    embed = discord.Embed(
        title="🧬CONSENT STATUS🧬",
        description=f"This Bot Was Made by Syntax-XXX a german Hobby Developer he habe this projekt for fun",
        color=discord.Color.gold()
    )
    embed.add_field(name="🧬 https://syntax-xxx.is-a.dev/", inline=False)
    embed.add_field(name="🧬 https://github.com/Syntax-XXX/", inline=False)
    embed.set_footer(text="🧬Made By Syntax-XXX")
    await ctx.reply(embed=embed)

@bot.command(name="serv-status")
@commands.check(lambda ctx: ctx.author.id == 970379709596729446)
async def check_server_status(ctx):
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime_delta = datetime.now() - boot_time
    uptime_str = str(uptime_delta).split('.')[0]
    cpu_usage = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    mem_str = f"{mem.used // (1024 ** 2)}MiB / {mem.total // (1024 ** 2)}MiB ({mem.percent}%)"
    disk_str = f"{disk.used // (1024 ** 3)}GB / {disk.total // (1024 ** 3)}GB ({disk.percent}%)"
    system = f"{platform.system()} {platform.release()} ({platform.machine()})"
    cpu = platform.processor()
    content = (
        "╭────────────────────────☘ ☘────────────────────────╮\n"
        f"💻 System     ➺ {system}\n"
        f"🧠 CPU        ➺ {cpu} ({cpu_usage}%)\n"
        f"📦 Memory     ➺ {mem_str}\n"
        f"💾 Disk       ➺ {disk_str}\n"
        f"⏳ Uptime     ➺ {uptime_str}\n"
        "╰────────────────────────☘ ☘────────────────────────╯")
    await ctx.reply(f"```{content}```")


bot.run(DISCORD_TOKEN)
