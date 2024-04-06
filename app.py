#!/bin/python3

from typing import Optional, Union, NamedTuple
from enum import Enum
import discord
from discord import app_commands
from discord.ext.commands import BucketType
import logging
import dotenv
import os
import asyncio
import time
import random
import datetime
import sqlalchemy
from sqlalchemy import create_engine, extract
from sqlalchemy.orm import sessionmaker
from models import User, Rolls, DoubleRolls, Base
import csv

# from gtts import gTTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


debug_users = [113555028207226880, 112675915145691136]
mod_roles = [634422998006235208]
data_users = [113555028207226880, 112675915145691136, 665557188298670140]
bots = [204255221017214977, 1100037608966459412]
sub_role = 600414478747828244
pit = 1053318611172859926
# pit=1162651881206726827


# load dotenv
dotenv.load_dotenv()

# load token
try:
    TOKEN = os.environ["TOKEN"]
except KeyError:
    logger.error(
        "No token found! Make sure you have a .env file with a TOKEN variable"
    )
    exit(1)

# load dev guild id if DEV is true
try:
    DEV_CHECK = False
    DEV_CHECK: bool = os.environ["DEV"].lower() == "true"
except KeyError:
    logger.info("Running in Production mode")

if DEV_CHECK is True:
    try:
        DEV = True
        MY_GUILD = discord.Object(id=int(os.environ["MY_GUILD"]))

    except KeyError:
        logger.info(
            "You are running in dev mode with no dev guild set, the fuck is wrong with you cunt?!"
        )
        exit(69)
else:
    DEV = False

# load database url
try:
    database_url = os.environ["DATABASEURL"]
except KeyError:
    logger.error(
        "No database url found! Make sure you have a .env file with a DATABASEURL variable"
    )
    exit(1)

# database_url="sqlite+pysqlite:///:memory:"

engine = create_engine(database_url, pool_use_lifo=True, pool_pre_ping=True)

Session = sessionmaker(bind=engine)
session = Session()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

Base.metadata.create_all(engine)


# DB functions
#region
def user_exists(user_id: int) -> bool:
    """
    Checks if the user exists in the database

    Args:
        user_id (int): Discord User ID

    Returns:
        bool: Existance of the user
    """
    user = session.query(User).filter_by(userid=user_id).first()
    if user:
        return True
    else:
        return False


def add_user(user_id: int, username: str) -> None:
    """
    Add a user to the database

    Args:
        user_id (int): Discord User ID
        username (str): Username of user
    """
    user = User(userid=user_id, username=username)
    session.add(user)
    session.commit()


def add_pronouns(user_id: int, pronouns: str) -> None:
    """
    Add pronouns to a user

    Args:
        user_id (int): Discord User ID
        pronouns (str): Pronouns of user
    """
    user = session.query(User).filter_by(userid=user_id).first()
    user.pronouns = pronouns  # type: ignore
    session.commit()


def insert_roll(user_id: int, roll: int, timestamp: datetime.datetime) -> None:
    """
    Insert a roll into the database

    Args:
        user_id (int): Discord User ID
        roll (int): The roll they rolled (1-12)
        timestamp (datetime.datetime): datetime of the roll
    """
    roll = Rolls(user_id=user_id, roll=roll, timestamp=timestamp)
    session.add(roll)
    session.commit()

def insert_doubleroll(user_id: int, timestamp: datetime.datetime) -> None:
    """
    Inserts a log of a user rolling multiple times in a day

    Args:
        user_id (int): Discord User ID
        timestamp (datetime.datetime): datetime of the roll
    """
    doubleroll = DoubleRolls(user_id=user_id, timestamp=timestamp)
    session.add(doubleroll)
    session.commit()


def remove_roll(user_id: int, timestamp: datetime.datetime, removed_by: int) -> None:
    """
    Remove a roll from the database

    Args:
        user_id (int): Discord User ID
        timestamp (datetime.datetime): datetime of the roll
        removed_by (int): Discord User ID of the user who removed the roll
    """
    roll = session.query(Rolls).filter_by(user_id=user_id, timestamp=timestamp).first()
    roll.roll_removed = True  # type: ignore
    roll.removed_by = removed_by  # type: ignore
    session.commit()


def update_username(user_id: int, username: str) -> None:
    """
    Update the username for a user

    Args:
        user_id (int): Discord User ID
        username (str): Username of user
    """
    user = session.query(User).filter_by(userid=user_id).first()
    user.username = username  # type: ignore
    session.commit()


def get_last_roll_timestamp(user_id: int) -> Optional[str]:
    """
    Get the last roll timestamp for a user

    Args:
        user_id (int): Discord User ID

    Returns:
        str or None: Timestamp of the last roll as a string or None
    """
    roll = (
        session.query(Rolls)
        .filter_by(user_id=user_id)
        .order_by(Rolls.timestamp.desc())
        .first()
    )
    if roll:
        return str(roll.timestamp)
    else:
        return None


def get_user_rolls(user_id: int, month: int, year: int):
    """
    Get all rolls for a given month and year for a user

    Args:
        user_id (int): Discord User ID of the user
        month (int): Month to get rolls for (1-12)
        year (int): Year to get rolls for

    Returns:
        List: _description_
    """
    rolls = (
        session.query(Rolls, User)
        .filter(
            extract("month", Rolls.timestamp) == month,
            extract("year", Rolls.timestamp) == year,
        )
        .filter(Rolls.user_id == user_id)
        .filter(Rolls.user_id == User.userid)
        .all()
    )
    rolls_list = []
    for roll in rolls:
        rolls_list.append(
            [
                roll.User.username,
                roll.Rolls.roll,
                roll.Rolls.timestamp,
                roll.Rolls.roll_removed if roll.Rolls.roll_removed else "Not Removed",
                roll.Rolls.removed_by if roll.Rolls.roll_removed else "Not Removed",
            ]
        )
    return rolls_list


def get_rolls(month: int, year: int):
    """
    Get all rolls for a given month and year

    Args:
        month (int): Month to get rolls for (1-12)
        year (int): Year to get rolls for

    Returns:
        list: A list of all rolls for the given month and year
    """
    # rolls = session.query(Rolls).filter(Rolls.timestamp.like(datetime.date(year=year,month=month))).all()
    rolls = (
        session.query(Rolls, User)
        .filter(
            extract("month", Rolls.timestamp) == month,
            extract("year", Rolls.timestamp) == year,
        )
        .filter(Rolls.user_id == User.userid)
        # .filter(Rolls.removed_by == User.userid)
        .all()
    )
    rolls_list = []
    for roll in rolls:
        rolls_list.append(
            [
                roll.User.username,
                roll.Rolls.roll,
                roll.Rolls.timestamp,
                roll.Rolls.roll_removed if roll.Rolls.roll_removed else "Not Removed",
                roll.Rolls.removed_by if roll.Rolls.roll_removed else "Not Removed",
            ]
        )
    return rolls_list

    # rolls = session.query(Rolls).filter(Rolls.timestamp.like(f"{year_month}%")).all()
    # rolls_list = []
    # for roll in rolls:
    #     rolls_list.append([roll.users.username, roll.roll, roll.timestamp, roll.removed, roll.removed_by.username if roll.removed_by else None])
    # return rolls_list


def get_all_rolls():
    """
    Get all rolls from the database

    Returns:
        list: A list of all rolls
    """
    rolls = session.query(Rolls, User).filter(Rolls.user_id == User.userid).all()
    rolls_list = []
    for roll in rolls:
        rolls_list.append(
            [
                roll.User.username,
                roll.Rolls.roll,
                roll.Rolls.timestamp,
                roll.Rolls.roll_removed,
                roll.Rolls.removed_by if roll.roll_removed else None,
            ]
        )
    return rolls_list

def get_double_rolls(month: int, year: int):
    """
    Get all double rolls for a given month and year

    Args:
        month (int): Month to get rolls for (1-12)
        year (int): Year to get rolls for

    Returns:
        list: A list of all double rolls for the given month and year
    """
    double_rolls = (
        session.query(DoubleRolls, User)
        .filter(
            extract("month", DoubleRolls.timestamp) == month,
            extract("year", DoubleRolls.timestamp) == year,
        )
        .filter(DoubleRolls.user_id == User.userid)
        .all()
    )
    double_rolls_list = []
    for roll in double_rolls:
        double_rolls_list.append(
            [
                roll.User.username,
                roll.DoubleRolls.timestamp,
            ]
        )
    return double_rolls_list

#endregion


# def seed_random(user_id: int, timestamp: datetime.datetime):
#     return f"{user_id}{timestamp.month}{timestamp.day}"


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(
            intents=intents,
            status=discord.Status.do_not_disturb,
            activity=discord.Game(name="some sick beats with ur dad"),
        )

        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        if DEV:
            self.tree.copy_global_to(guild=MY_GUILD)
            await self.tree.sync(guild=MY_GUILD)
            # self.tree.copy_global_to(guild=TEST_GUILD)
            # await self.tree.sync(guild=TEST_GUILD)
            logger.info("Copied global commands to dev guilds")
        else:
            await self.tree.sync()


bot = MyClient(intents=intents)


# Bot events
@bot.event
async def on_ready():
    logger.info(f"{bot.user} has connected to Discord!")
    logger.info(
        f"Invite URL is: https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=0&scope=bot%20applications.commands"  # type: ignore
    )


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, exception: app_commands.AppCommandError
):
    """
    Error handler for app commands

    Args:
        interaction (discord.Interaction): Disocrd interaction
        exception (app_commands.AppCommandError): The exception that was raised
    """
    if isinstance(exception, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"You are on cooldown, try again in {round(exception.retry_after, 2)} seconds",
            ephemeral=True,
        )
        logging.info(
            f"{interaction.user.name} tried to use a command on cooldown. This has been logged for debug purposes"
        )
        return
    else:
        logging.error(f"{interaction.command.name} raised an exception: {exception}")  # type: ignore
        try:
            await interaction.response.defer(ephemeral=True)
        except discord.errors.InteractionResponded:
            pass

        await interaction.followup.send(
            f"Something went wrong! Tell Dingo to fucking fix it <:Madge:786617980103688262>",
            ephemeral=True,
        )
        return


# cooldown handler
def cooldown_handler(
    interaction: discord.Interaction,
) -> Optional[app_commands.Cooldown]:
    """Bypasses the cooldown for the owner and other admins, otherwise returns the cooldown."""
    # user = get_user(interaction.user.id)
    if interaction.user.id in debug_users:  # type: ignore # user is not none
        return None
    return app_commands.Cooldown(1, 600)


# TLDR command that submits a job to the queue
# @bot.tree.command()
# @app_commands.checks.cooldown(1,600, key=lambda i: (i.guild_id, i.user.id))
# @app_commands.guild_only()
# @app_commands.rename(num_messages="number")
# @app_commands.describe(num_messages="Number of messages to summarise")
# @app_commands.describe(tts="Not actually implemented. Maybe later")
# async def tldr(interaction: discord.Interaction, num_messages: int = 500, tts: bool = False):
#     """
#     Creates a TLDR of the last n messages.
#     """
#     start_time = time.time()
#     if num_messages < 10:
#         await interaction.response.send_message(f"{interaction.author.mention} Please enter a number greater than 10! or I will find where you live <:Madge:786617980103688262>")
#         return
#     if num_messages > 500:
#         # return ephemeral message
#         await interaction.response.send_message("Please enter a number less than 500! <:Madge:786617980103688262>", ephemeral=True)
#         logging.info(interaction.user.name + " tried to generate a summary with " + num_messages + "messages")
#         return


#     messages = [message async for message in interaction.channel.history(limit=num_messages)]
#     extracted = []
#     for message in messages:
#         if message.author.id in bots:
#             continue
#         extracted.append(
#             f'{message.author.display_name} : {message.content} \n')
#     extracted.reverse()
#     text = ''.join(str(value) for value in extracted)
#     await interaction.response.send_message("Messages have been sent to the job queue! I will eventually post the summary here 🤖")
#     followup = interaction.followup
#     logging.debug(followup)

# # if TTS is true then convert summary to speech and post as file
# if tts:
#     tts = gTTS(summary)
#     tts.save("summary.mp3")
#     await ctx.respond(file=discord.File("summary.mp3"))

# @bot.slash_command(name="params", description="Returns the parameters of the summarizer")
# async def params(ctx):
#     await ctx.respond(summarizer.get_inference_params())


@bot.tree.command()
async def ping(interaction: discord.Interaction):
    """
    Gets the ping from the bot to discord's gateway
    """
    await interaction.response.send_message(
        f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True
    )


class Units(Enum):
    """
    All the units that can be converted to Nikez
    """

    Metres = 1
    Centimetres = 0.01
    Milimetres = 0.001
    Kilometres = 1000
    Inches = 0.0254
    Feet = 0.3048
    Yards = 0.9144
    Miles = 1609.34
    NauticalMiles = 1852


# @bot.slash_command(name="convert", description="Converts units to Nikez", cooldown=CooldownMapping(Cooldown(1, 600), BucketType.user), on_application_command_error=on_application_command_error)
@bot.tree.command()
# @app_commands.checks.cooldown(1,600, key=lambda i: (i.guild_id, i.user.id))
@app_commands.checks.dynamic_cooldown(cooldown_handler)
@app_commands.guild_only()
@app_commands.describe(num="Number to convert")
@app_commands.describe(unit="Unit to convert")
async def convertnikez(interaction: discord.Interaction, num: float, unit: Units):
    """
    Converts units to Nikez
    """
    # check user is in sub role
    if sub_role not in [role.id for role in interaction.user.roles]:  # type: ignore
        await interaction.response.send_message(
            "You must be a subscriber to use this command", ephemeral=True
        )
        return
    if num < 0:
        await interaction.response.send_message("Invalid number", ephemeral=True)
        return
    if unit not in Units:
        await interaction.response.send_message(
            "Invalid units, Yell at Dingo to add them", ephemeral=True
        )
        return

    logging.info(
        f"{interaction.user.name} converted {num} {unit.name}:{unit.value} to Nikez"
    )
    # calculate conversion
    converted = num * unit.value / 1.87
    await interaction.response.send_message(f"{num} {unit.name} is {converted} Nikez")


# pitroll, can only be run in the pit channel
# @bot.slash_command(name="pitroll", description="Rolls a random number between 1 and 12")
@bot.tree.command()
# @app_commands.checks.cooldown(1,600, key=lambda i: (i.guild_id, i.user.id))
@app_commands.checks.dynamic_cooldown(cooldown_handler)
@app_commands.guild_only()
async def pitroll(interaction: discord.Interaction):
    """
    Rolls your number between 1 and 12 🙂
    """
    timestamp = datetime.datetime.now()

    # await ctx.respond("Ignore this. Discord hates Dingo", ephemeral=True)
    if interaction.channel.id != pit:  # type: ignore
        await interaction.response.send_message(
            (
                "YOU JUST ROLLED A 1 YOU FUCKING BITCH"
                if random.randint(1, 100) == 69
                else "<:Madge:786617980103688262> Only in the pit! This has been logged so we can call you an idiot."
            ),
            ephemeral=True,
        )
        logging.info(f"{interaction.user.name} tried to use pitroll in {interaction.channel.name}")  # type: ignore
        return

    await interaction.response.defer()
    followup = interaction.followup
    # seed random user id and current date
    # random.seed(timestamp.day + timestamp.month + timestamp.year+interaction.user.id)
    random.seed(interaction.user.id + timestamp.day + timestamp.month + timestamp.year)
    roll = random.randint(1, 12)

    random.seed()  # reset random

    # '2023-06-09 15:18:43.526048' format
    last_roll_str = get_last_roll_timestamp(interaction.user.id)
    logging.info(f"Last roll for {interaction.user.name} was {last_roll_str}")
    last_roll_time = (
        datetime.datetime.strptime(last_roll_str, "%Y-%m-%d %H:%M:%S.%f")
        if last_roll_str  # checks if last_roll_str has a value, else set date to 0 epoch
        else datetime.datetime(1970, 1, 1)
    )

    # check if last roll was today, they reset at 00:00:00
    if last_roll_time.date() == timestamp.date():
        rat = last_roll_time + datetime.timedelta(days=1)
        roll_again_midnight = datetime.datetime(rat.year, rat.month, rat.day)

        await followup.send(
            f"{interaction.user.display_name} already rolled today! Try again <t:{int(roll_again_midnight.timestamp())}:R> {' BITCH!' if random.randint(1,100) == 69 else ''}",
            ephemeral=True,
        )
        insert_doubleroll(interaction.user.id, timestamp)
        return
    # post roll text
    post_roll_text = ""
    reaction = []
    if roll <= 5:
        if roll == 1:
            roll_1_rng = random.randint(1, 100)
            post_roll_text = (
                "<a:NikezRipBozo:1018348131643052172>"
                if roll_1_rng
                == 69  # if roll rng is 69 then trigger funni else show hug
                else "\U0001fac2"
            )
            reaction = (
                ["a:NikezRipBozo:1018348131643052172"]
                if roll_1_rng
                == 69  # if roll rng is 69 then trigger funni else show hug
                else ["\U0001fac2"]
            )
        else:
            post_roll_text = "\U0001fac2"
            reaction = ["\U0001fac2"]
    elif roll == 6:
        post_roll_text = "<:nikezSus:1091173163687235656>"
        reaction = [":nikezSus:1091173163687235656"]
    elif 7 <= roll <= 9:
        post_roll_text = "<:LipBite:1061396815993381014>"
        reaction = [":LipBite:1061396815993381014"]
        # if random.randint(1, 100) <= 6:
        #     reaction.append("a:Hola:1210319687578292224")
    elif roll >= 10:
        post_roll_text = "<:LipBite:1061396815993381014>"
        reaction = [":LipBite:1061396815993381014", "a:nikezSexo:1195442963577327727"]

    # check if date is april first, if so everyone rolls a 1 :SMILE:
    if timestamp.month == 4 and timestamp.day == 1:
        april_first_rng = random.randint(1, 100)
        post_roll_text = "<a:NikezRipBozo:1018348131643052172>" if april_first_rng >= 69 else "\U0001fac2"
        message = await followup.send(
            f"{interaction.user.display_name} rolled a 1 {post_roll_text}", wait=True
        )
        await message.add_reaction(
            "a:NikezRipBozo:1018348131643052172"
            if april_first_rng >= 69
            else "\U0001fac2"
        )

    else:
        message = await followup.send(
            f"{interaction.user.display_name} rolled a {roll} {post_roll_text}",
            wait=True,
        )
        # add reaction to sent message
        # await message.add_reaction(reaction)
        for react in reaction:
            await message.add_reaction(react)

    # check if user exists already in DB
    user = user_exists(interaction.user.id)
    if not user:
        add_user(interaction.user.id, interaction.user.name)
    update_username(interaction.user.id, interaction.user.name)
    insert_roll(interaction.user.id, roll, timestamp)


class Months(Enum):
    """
    All the months of the year
    """

    January = 1
    February = 2
    March = 3
    April = 4
    May = 5
    June = 6
    July = 7
    August = 8
    September = 9
    October = 10
    November = 11
    December = 12


# @bot.slash_command(name="pitdata", description="Amy's command", on_application_command_error=on_application_command_error)
@bot.tree.command()
@app_commands.describe(month="Month to choose")
@app_commands.describe(year="The year you want to get data for. Defaults to this year")
async def pitdata(
    interaction: discord.Interaction,
    month: Months,
    year: int = datetime.datetime.now().year,
):
    """
    Amy's command
    """
    if (interaction.user.id in data_users) or (
        mod_roles in [role.id for role in interaction.user.roles]  # type: ignore
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)
        followup = interaction.followup
        # await interaction.respond("🤖 🖨️ for "+ month + " of " + str(year), ephemeral=True)
        # get index of chosen month
        months_rolls = get_rolls(month.value, year)
        double_months_rolls = get_double_rolls(month.value, year)
        logging.info(
            f"{interaction.user.display_name} used pitdata for {month} of {str(year)}"
        )
        # turn month_rolls object into csv
        with open("rolls.csv", "w") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["User", "Roll", "Timestamp", "Removed", "Removed By"])
            for row in months_rolls:
                writer.writerow(row)
        with open("doublerolls.csv", "w") as double_csv_file:
            writer = csv.writer(double_csv_file)
            writer.writerow(["User", "Timestamp"])
            for row in double_months_rolls:
                writer.writerow(row)
        await followup.send(
            "🤖 🖨️ *printing noises*", files=[discord.File("rolls.csv"), discord.File("doublerolls.csv")], ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "<:Madge:786617980103688262> You just rolled a 1 BITCH"
        )
        logging.info(
            interaction.user.display_name
            + " tried to use pitdata. Remind them that they a bitch NODDERS"
        )


# Admin shittery

# admin tldr: NO RULES
# @bot.slash_command(name="newspaper", description="Is this a newspaper? or is this just bot abuse?")
# @bot.tree.command()
# @app_commands.describe(num_messages="Number of messages")
# async def newspaper(interaction: discord.Interaction, num_messages: int=500):
#     if interaction.user.id in debug_users or mod_roles in [role.id for role in interaction.user.roles]:
#         start_time = time.time()
#         await interaction.respond("🖨 📰")
#         followup = interaction.followup
#         messages = [message async for message in interaction.channel.history(limit=num_messages)]
#         extracted = []
#         for message in messages:
#             if message.author.id in bots:
#                 continue
#             extracted.append(
#                 f'{message.author.display_name} : {message.content} \n')
#         extracted.reverse()
#         text = ''.join(str(value) for value in extracted)
#         summary = await generate_summ(text)
#         time_taken = str(time.time() - start_time)
#         logging.info(interaction.user.display_name + " generated a newspaper with a length of " + str(len(summary)) + " in " + time_taken + " seconds")
#         with open("📰.txt", "w") as f:
#             f.write(summary)
#         await followup.send("📰", file=discord.File("📰.txt", filename="📰.txt"))
#     else:
#         await interaction.response.send_message("Stop trying to take my bit! <:Madge:786617980103688262>")


# DEBUGGING STUFF


# @bot.slash_command(name="debug", description="Debugging command")
@bot.tree.command()
@app_commands.describe(bozo_points="fuck")
async def debug(interaction: discord.Interaction, bozo_points: int = 500):
    """
    Admin fuckery
    """
    if interaction.user.id in debug_users:
        await interaction.response.defer(ephemeral=True, thinking=True)
        followup = interaction.followup
        messages = [
            message async for message in interaction.channel.history(limit=bozo_points)  # type: ignore
        ]
        extracted = []
        for message in messages:
            if message.author.id in bots:
                continue
            extracted.append(f"{message.author.display_name} : {message.content} \n")
        extracted.reverse()
        text = "".join(str(value) for value in extracted)
        with open("debug.txt", "w") as f:
            f.write(text)
        await followup.send(
            "Here you go:", file=discord.File("debug.txt"), ephemeral=True
        )
    else:
        logging.info(
            f"{interaction.user.name} tried to use the debug command, This incident has been reported"
        )
        await interaction.response.send_message(
            f"{interaction.user.name} is not in the sudoers file.  This incident will be reported.",
            ephemeral=True,
        )


@bot.tree.command()
async def rollfordeath(interaction: discord.Interaction):
    """
    Rolls for perma
    """
    # check if user is debug user
    if interaction.user.id in debug_users:
        await interaction.response.defer()
        followup = interaction.followup
        random.seed()
        roll = random.randint(1, 2)
        if roll == 1:
            await followup.send(f"{interaction.user.display_name} rolled a 1, HE LIVES")
        else:
            await followup.send(f"{interaction.user.display_name} rolled a 2, HE DEAD")
        logging.info(
            f"{interaction.user.display_name} rolled a {roll}, 1 is live, 2 is dead"
        )
    else:
        await interaction.response.send_message(
            f"https://cdn.discordapp.com/attachments/208531692720226304/1206931006158807091/fucking_soiled_it.mp4?ex=65f97c97&is=65e70797&hm=11d2c92573c7eca054d8c707ddb425ce68d281d518ef0f4f1b0cc33c5b927343&",
            ephemeral=True,
        )


# @bot.slash_command(name="debug_hidden", description="Debugging command")
# @bot.tree.command()
# async def debug_hidden(interaction: discord.Interaction):
#     if interaction.user.id in debug_users:
#         await interaction.response.send_message(f"{interaction.user.display_name} is in the sudoers file.  This incident will not be reported.", ephemeral=True)
#     else:
#         await interaction.response.send_message(f"{interaction.user.display_name} is not in the sudoers file.  This incident will be reported.", ephemeral=True)


bot.run(TOKEN)
