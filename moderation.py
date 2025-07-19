import discord
from discord.ext import commands, tasks
from discord import app_commands
import os, json, re
from datetime import datetime, timedelta

MODLOG_PATH = "./Database/Moderation"
STAFF_ROLE_ID = 1217757004630855792


def ensure_guild_directory(guild_id):
    path = os.path.join(MODLOG_PATH, str(guild_id))
    os.makedirs(path, exist_ok=True)
    return path


def get_next_case_id(guild_id):
    path = ensure_guild_directory(guild_id)
    existing = [f for f in os.listdir(path) if f.startswith("case_") and f.endswith(".json")]
    return len(existing) + 1


def write_case(guild_id, case_id, data):
    path = ensure_guild_directory(guild_id)
    with open(os.path.join(path, f"case_{case_id}.json"), "w") as f:
        json.dump(data, f, indent=4)


def load_case(guild_id, case_id):
    path = ensure_guild_directory(guild_id)
    with open(os.path.join(path, f"case_{case_id}.json")) as f:
        return json.load(f)


def delete_case(guild_id, case_id):
    path = ensure_guild_directory(guild_id)
    os.remove(os.path.join(path, f"case_{case_id}.json"))


def parse_duration(duration_str):
    match = re.match(r"(?i)(\d+)([mhdw])", duration_str.strip())
    if not match:
        return None
    num, unit = match.groups()
    return {
        "m": timedelta(minutes=int(num)),
        "h": timedelta(hours=int(num)),
        "d": timedelta(days=int(num)),
        "w": timedelta(weeks=int(num))
    }.get(unit.lower())


def format_duration(duration):
    if not duration:
        return "N/A"
    if isinstance(duration, str):
        duration = parse_duration(duration)
    if not duration:
        return "N/A"
    total = int(duration.total_seconds())
    if total % 604800 == 0:
        return f"{total // 604800} Week(s)"
    if total % 86400 == 0:
        return f"{total // 86400} Day(s)"
    if total % 3600 == 0:
        return f"{total // 3600} Hour(s)"
    if total % 60 == 0:
        return f"{total // 60} Minute(s)"
    return str(duration)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.unban_loop.start()
        self.unmute_loop.start()

    async def cog_check(self, ctx):
        return any(r.id == STAFF_ROLE_ID for r in ctx.author.roles)

    async def punish(self, guild, member, moderator, action, reason, duration=None, appealable=None):
        case_id = get_next_case_id(guild.id)
        timestamp = datetime.utcnow().strftime("%m/%d/%Y %I:%M %p")
        duration_str = format_duration(duration)

        case_data = {
            "action": action,
            "moderator": moderator.id,
            "member": member.id,
            "reason": reason,
            "duration": duration_str,
            "appealable": appealable or "N/A",
            "timestamp": timestamp
        }
        if duration_str != "N/A" and isinstance(duration, timedelta):
            case_data["end_time"] = (datetime.utcnow() + duration).isoformat()

        write_case(guild.id, case_id, case_data)

        try:
            await member.send(
                f"Dear {member.mention}, you have been **{action}** for **{reason}**.\n"
                f"Duration: **{duration_str}**\nCase No: **#{case_id}**. Contact staff if needed."
            )
        except:
            pass

        embed = discord.Embed(title=f"{action} | Case #{case_id}", color=discord.Color.orange())
        embed.add_field(name="Member", value=f"{member.mention} ({member.id})")
        embed.add_field(name="Moderator", value=f"<@{moderator.id}> ({moderator.id})")
        embed.add_field(name="Duration", value=duration_str)
        embed.add_field(name="Reason", value=reason)
        if appealable:
            embed.add_field(name="Appealable", value=appealable)
        embed.set_footer(text=timestamp)

        modlog = discord.utils.get(guild.text_channels, name="mod-logs")
        if modlog:
            await modlog.send(embed=embed)

    @commands.hybrid_command(name="warn", description="Warn a user")
    @app_commands.describe(user="User to warn", reason="Reason")
    async def warn(self, ctx, user: discord.Member, *, reason: str):
        try:
            await self.punish(ctx.guild, user, ctx.author, "Warned", reason)
            await ctx.send(f"✅ {user.mention} has been warned.")
        except Exception as e:
            await ctx.send(f"❌ Failed to warn: {e}")

    @commands.hybrid_command(name="mute", description="Mute a user temporarily")
    @app_commands.describe(user="User to mute", duration="Duration (e.g. 30m, 1h)", reason="Reason")
    async def mute(self, ctx, user: discord.Member, duration: str, *, reason: str):
        parsed = parse_duration(duration)
        if not parsed:
            await ctx.send("❌ Invalid duration format.")
            return
        try:
            await user.timeout(parsed, reason=reason)
            await self.punish(ctx.guild, user, ctx.author, "Muted", reason, parsed)
            await ctx.send(f"🔇 {user.mention} muted for {format_duration(parsed)}")
        except Exception as e:
            await ctx.send(f"❌ Failed to mute: {e}")

    @commands.hybrid_command(name="unmute", description="Unmute a user")
    @app_commands.describe(user="User to unmute", reason="Reason")
    async def unmute(self, ctx, user: discord.Member, *, reason: str):
        try:
            await user.timeout(None, reason=reason)
            await self.punish(ctx.guild, user, ctx.author, "Unmuted", reason)
            await ctx.send(f"✅ {user.mention} has been unmuted.")
        except Exception as e:
            await ctx.send(f"❌ Failed to unmute: {e}")

    @commands.hybrid_command(name="kick", description="Kick a user")
    @app_commands.describe(user="User to kick", reason="Reason")
    async def kick(self, ctx, user: discord.Member, *, reason: str):
        try:
            await user.kick(reason=reason)
            await self.punish(ctx.guild, user, ctx.author, "Kicked", reason)
            await ctx.send(f"👢 {user.mention} has been kicked.")
        except Exception as e:
            await ctx.send(f"❌ Failed to kick: {e}")

    @commands.hybrid_command(name="ban", description="Ban a user")
    @app_commands.describe(user="User to ban", duration="Duration or permanent", reason="Reason", appealable="Is appealable?")
    async def ban(self, ctx, user: discord.Member, duration: str, reason: str, appealable: str = "N/A"):
        parsed = parse_duration(duration)
        if not parsed and duration.lower() not in ["perm", "permanent"]:
            await ctx.send("❌ Invalid duration format.")
            return
        try:
            await user.ban(reason=reason)
            await self.punish(ctx.guild, user, ctx.author, "Banned", reason, None if duration.lower().startswith("perm") else parsed, appealable)
            await ctx.send(f"🔨 {user.mention} has been banned.")
        except Exception as e:
            await ctx.send(f"❌ Failed to ban: {e}")

    @commands.hybrid_command(name="unban", description="Unban a user")
    @app_commands.describe(user_id="ID of the banned user", reason="Reason")
    async def unban(self, ctx, user_id: int, *, reason: str):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            await self.punish(ctx.guild, user, ctx.author, "Unbanned", reason)
            await ctx.send(f"✅ {user} has been unbanned.")
        except Exception as e:
            await ctx.send(f"❌ Failed to unban: {e}")

    @commands.hybrid_command(name="softban", description="Softban a user")
    @app_commands.describe(user="User to softban", reason="Reason")
    async def softban(self, ctx, user: discord.Member, *, reason: str):
        try:
            await ctx.guild.ban(user, reason=reason)
            await ctx.guild.unban(user, reason="Softban")
            await self.punish(ctx.guild, user, ctx.author, "Softbanned", reason)
            await ctx.send(f"🚫 {user.mention} was softbanned.")
        except Exception as e:
            await ctx.send(f"❌ Failed to softban: {e}")

    @commands.hybrid_command(name="user-moderation", description="View moderation history of a user")
    @app_commands.describe(user="User to lookup")
    async def user_moderation(self, ctx, user: discord.User):
        path = ensure_guild_directory(ctx.guild.id)
        cases = []
        for f in os.listdir(path):
            with open(os.path.join(path, f)) as file:
                data = json.load(file)
                if str(data.get("member")) == str(user.id):
                    cases.append((f, data))

        if not cases:
            await ctx.send("No moderation cases found for this user.")
            return

        embed = discord.Embed(title=f"Moderation History for {user}", color=discord.Color.blue())
        for fname, data in sorted(cases):
            embed.add_field(
                name=f"Case {fname.split('_')[1].split('.')[0]}",
                value=f"**{data['action']}** - {data['reason']} - {data['timestamp']}",
                inline=False
            )
        await ctx.send(embed=embed)

    @app_commands.command(name="edit-case", description="Edit a mod case")
    @app_commands.describe(case_id="Case number", field="Field to edit", value="New value")
    async def edit_case(self, interaction: discord.Interaction, case_id: int, field: str, value: str):
        try:
            data = load_case(interaction.guild.id, case_id)
            data[field] = value
            write_case(interaction.guild.id, case_id, data)
            await interaction.response.send_message(f"✅ Case #{case_id} updated.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Failed to edit case.", ephemeral=True)

    @app_commands.command(name="delete-case", description="Delete a mod case")
    @app_commands.describe(case_id="Case number to delete")
    async def delete_case(self, interaction: discord.Interaction, case_id: int):
        try:
            delete_case(interaction.guild.id, case_id)
            await interaction.response.send_message(f"🗑️ Case #{case_id} deleted.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Failed to delete case.", ephemeral=True)

    @app_commands.command(name="view-case", description="View a specific case")
    @app_commands.describe(case_id="Case number to view")
    async def view_case(self, interaction: discord.Interaction, case_id: int):
        try:
            case = load_case(interaction.guild.id, case_id)
            embed = discord.Embed(title=f"📁 Case #{case_id}", color=discord.Color.blue())
            for key, value in case.items():
                embed.add_field(name=key.capitalize(), value=str(value), inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.response.send_message("❌ Failed to load case.", ephemeral=True)

    @tasks.loop(minutes=1)
    async def unban_loop(self):
        for guild in self.bot.guilds:
            path = ensure_guild_directory(guild.id)
            for file in os.listdir(path):
                with open(os.path.join(path, file)) as f:
                    data = json.load(f)
                if data.get("action") == "Banned" and "end_time" in data:
                    if datetime.utcnow() > datetime.fromisoformat(data["end_time"]):
                        user = await self.bot.fetch_user(data["member"])
                        await guild.unban(user, reason="Auto-unban")
                        data["action"] = "Unbanned"
                        write_case(guild.id, int(file.split("_")[1].split(".")[0]), data)
                        channel = discord.utils.get(guild.text_channels, name="mod-logs")
                        if channel:
                            await channel.send(f"✅ User {user.mention} was automatically unbanned. Case updated.")

    @tasks.loop(minutes=1)
    async def unmute_loop(self):
        for guild in self.bot.guilds:
            path = ensure_guild_directory(guild.id)
            for file in os.listdir(path):
                with open(os.path.join(path, file)) as f:
                    data = json.load(f)
                if data.get("action") == "Muted" and "end_time" in data:
                    if datetime.utcnow() > datetime.fromisoformat(data["end_time"]):
                        member = guild.get_member(data["member"])
                        if member:
                            await member.timeout(None, reason="Auto-unmute")
                            data["action"] = "Unmuted"
                            write_case(guild.id, int(file.split("_")[1].split(".")[0]), data)
                            channel = discord.utils.get(guild.text_channels, name="mod-logs")
                            if channel:
                                await channel.send(f"✅ {member.mention} was automatically unmuted. Case updated.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
