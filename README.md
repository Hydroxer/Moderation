# Moderation
Moderation.py is a free Moderation module 

# Installation Guide

To add moderation.py into your Bot as a Cog.
1. Download the zip file or use
```sudo
git clone https://github.com/Corwindev/Discord-Bot.git
```

3. Create a foler named Cogs in your project file or inside your directory.
4. Add Moderation.py into your Cogs folder.
5. Paste the code provided below in your main file (i.e. Main.py)

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
