# 🛡️ Moderation Cog for Discord Bots

`Moderation.py` is a modular, ready-to-use moderation extension (Cog) for Discord bots built using [discord.py](https://github.com/Rapptz/discord.py).  
It provides essential moderation tools with case tracking, logging, and permission control.

> ⚙️ Only users with the configured **Staff Role ID** will be able to use the moderation commands.

---

## 📦 Features

- 🔧 Slash and prefix command support  
- 📁 Case-based moderation logging  
- 🚫 Supports warn, mute, kick, ban, unban, and softban  
- 🔐 Role-based permission control (editable in the script header)  
- 🧩 Designed to be easily integrated into existing bots  

---

## 📥 Installation Guide

Follow these steps to integrate `Moderation.py` into your bot:

### 1. Clone the Repository

```bash
git clone https://github.com/Hydroxer/Moderation.git
```

Or [download the ZIP](https://github.com/Hydroxer/Moderation/archive/refs/heads/main.zip) and extract it manually.

---

### 2. Project Setup

1. Inside your bot's root directory, create a folder named `cogs`:
    ```bash
    mkdir cogs
    ```
2. Move `Moderation.py` into the `cogs/` directory.

3. Also create a folder named `Moderations` in the root directory. This will store moderation case files and logs:
    ```bash
    mkdir Moderations
    ```

---

### 3. Load the Cog in Your Bot

In your `main.py` or entry file, add the following coroutine to dynamically load all cogs from the `cogs` folder:

```python
import os

async def load_all_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded: cogs.{filename[:-3]}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")
```

Then, call it before starting the bot:

```python
import asyncio

asyncio.run(load_all_extensions())
bot.run("YOUR_TOKEN")
```

---

## ⚠️ Requirements

- Python 3.8+
- `discord.py` v2.0+ (with `app_commands` support)

---

## 🧠 Configuration Notes

At the top of `Moderation.py`, you will find:

```python
STAFF_ROLE_ID = 123456789012345678
```

Replace `123456789012345678` with your **Moderator** or **Staff** role ID.  
Only members with this role will have access to the moderation commands.

---

## 🪪 License

This project is licensed under the MIT License.  
Feel free to use, modify, and integrate it into your own projects.

---

## 📫 Contact

Developed by [Hydroxer](https://github.com/Hydroxer)  
For bugs or suggestions, please open an issue or submit a pull request.
