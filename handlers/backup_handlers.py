import asyncio
import os
import shutil
import time

from db import DB


async def backup_command(message, command_arg):
    if command_arg is None:
        await message.channel.send("Must specify a backup file. Will be given a .dmp extension if it doesn't have one already")
        return
    filename = command_arg.split()[0]
    if filename.lower().endswith('.dmp'):
        filename = filename[:-4]
    # Make sure all pending changes saved
    while DB.save_queue.qsize() > 0:
        await asyncio.sleep(.5)
    shutil.copy('save.dmp', f'{filename}.dmp')
    await message.channel.send(f'Saved backup to {filename}.dmp')


async def list_backups_command(message, command_arg):
    available_backups = []
    for filename in os.listdir('.'):
        if filename.lower().endswith('.dmp') and filename != 'save.dmp':
            available_backups.append(filename)
    if len(available_backups) > 0:
        available_backups = '\n'.join(available_backups)
        await message.channel.send(f"Available backups:```\n{available_backups}```")
    else:
        await message.channel.send(f"No available backups")


async def restore_command(message, command_arg):
    if command_arg is None:
        await message.channel.send('Must specify a backup file. Use `list-backups` to see available backups')
        return
    filename = command_arg.split()[0]
    if not filename.endswith('.dmp'):
        filename += '.dmp'
    if not os.path.isfile(filename):
        await message.channel.send(f'File {filename} does not exist')
        return
    backup_filename = f'save-{time.time()}.dmp'
    shutil.copy('save.dmp', backup_filename)  # Backup old save file
    await message.channel.send(f'Backed up current save file to {backup_filename}')
    await DB.load_from_disk(filename)
    await message.channel.send(f'Successfully restored backup from {filename}')
