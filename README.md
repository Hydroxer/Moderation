# Moderation
Moderation.py is a free Moderation module for your discord bot. it is based as a Cog. Its easy and simple to use.
You can change your staff Role ID in the Header, only Role ID you have pasted there will have the permission to access to the module(which can be your Staff or Moderator Role).

# Installation Guide

To add moderation.py into your Bot as a Cog.
1. Download the zip file or use
```sudo
git clone https://github.com/Hydroxer/Moderation.git
``` 
3. Extract the zip into your Bot's Project Directory.

4. Create a folder named **Cogs** inside project file or inside your directory.
5. Add **Moderation.py** into your Cogs folder.
6. Paste the code provided below in your main file (i.e. Main.py)

```
async def load_all_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded: cogs.{filename[:-3]}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")
```

Please add the code at the ending of the file, above the Run Fuction.

6. Create a Folder named named **Moderations** for Storing the Modlogs.

*Only usable for Python and Discord.py*
