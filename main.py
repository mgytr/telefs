#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from typing import NoReturn
import os
import sys
from telegram import Bot
from telegram.error import BadRequest
from dotenv import load_dotenv
from asyncio import new_event_loop, set_event_loop, run
import io
import json

import logging
import time
from argparse import ArgumentParser


"""
A FUSE filesystem that uses Telegram as a backend.
"""

def reloaddb():
    global db
    db = json.load(open('fs.json'))
def savedb():
    with open('fs.json', 'w') as f:
        f.write(json.dumps(db))
try:
    load_dotenv('.env')
except FileNotFoundError:
    print('No .env file found. Please fill in the variables.')
    open('.env', 'w').write('TOKEN="BOT_TOKEN_HERE"\nCHATID="CHAT_ID_HERE"')

    exit(1)
try:
    db = json.load(open('fs.json'))
except FileNotFoundError:
    print('No fs.json file found. Creating.')
    db = [{}, [], {}]
    savedb()




token = os.environ['TOKEN']
chatid = os.environ['CHATID']

def getiofrompath(path: str):
    async def f():
        bot = Bot(token=token)
        out = io.BytesIO()
        if db[0][path] != None:
            await ((await bot.get_file(db[0][path])).download_to_memory(out))
        else:
            out.write(b'')
        out.seek(0)
        return out
    return run(f())
def writepath(path: str, content: bytes):
    async def f():
        global db
        bot = Bot(token=token)
        if path in db[0].keys():
            del db[0][path]
        try:
            msg = await bot.send_document(chatid, content)
    
            db[0][path] = msg.document.file_id
            print(msg, msg.document.file_id)
            savedb()
        except BadRequest:
            db[0][path] = None

    return run(f())

# FUSE filesystem
from fuse import FUSE, FuseOSError, Operations
from stat import S_IFDIR, S_IFREG
from errno import ENOENT

class TelegramFUSE(Operations):
    def __init__(self):
        self.buffers = {} 

    def getattr(self, path, fh=None):
        if not path in db[2].keys() and (path in db[1] + ['/'] or path in db[0]):
            self.utimens(path)
        if path in db[1] + ['/']:
            return dict(st_mode=(S_IFDIR | 0o755), st_nlink=2, st_atime=db[2][path][0], st_mtime=db[2][path][1], st_ctime=0)
        elif path in db[0]:
            return dict(st_mode=(S_IFREG | 0o755), st_nlink=1, st_size=getiofrompath(path).getbuffer().nbytes, st_atime=db[2][path][0], st_mtime=db[2][path][1], st_ctime=0)
        raise FuseOSError(ENOENT)

    def readdir(self, path, fh):
        files = ['.', '..']
        if not path in db[1] + ['/']: raise FuseOSError(ENOENT)
        for x in db[0]:
            if path == '/' and x.count('/') == 1:
                files.append(x[1:])
            elif path != '/' and '/'.join(x.split('/')[:-1]) == path:
                files.append(x.split('/')[-1])
        for x in db[1]:
            if path == '/' and x.count('/') == 1:
                files.append(x[1:])
            elif path != '/' and '/'.join(x.split('/')[:-1]) == path:
                files.append(x.split('/')[-1])
        print(files)
        return files
    def open(self, path, fi):
        if not path in db[0]: raise FuseOSError(ENOENT)
        return 0
    def read(self, path, size, offset, fh):
        v = getiofrompath(path).getvalue()[offset:offset+size]

        return v

    def write(self, path, data, offset, fh=None):
        
        if path not in db[0]: raise FuseOSError(ENOENT)

        if path not in self.buffers:
            self.buffers[path] = (getiofrompath(path).getvalue() if path in db[0].keys() else b'')
        
        self.buffers[path] = (self.buffers[path][:offset] if offset > 0 else self.buffers[path]) + data + (self.buffers[path][offset + len(data):] if offset + len(data) < len(self.buffers[path]) else b'')

        return len(data)

    def create(self, path, fi=None):
        if path in db[0].keys(): raise FuseOSError(ENOENT)
        db[0][path] = None
        return 0

    def mkdir(self, path, _=None):
        if path in db[1]: raise FuseOSError(ENOENT)
        db[1].append(path)
        savedb()
        return 0

    def unlink(self, path):
        if path in db[0]:
            del db[0][path]
        else:
            raise FuseOSError(ENOENT)
        savedb()
        return 0

    def rmdir(self, path):
        if path not in db[1]: raise FuseOSError(ENOENT)
        db[1].remove(path)
        savedb()
        return 0

    def rename(self, old, new):
        if old in db[0]:
            db[0][new] = db[0][old]
            del db[0][old]
        else:
            raise FuseOSError(ENOENT)
        savedb()
        return 0

    def truncate(self, path, length):
        truncated = getiofrompath(path).getvalue()[:length].ljust(
        length, '\x00'.encode('ascii'))
        if path not in db[0]: raise FuseOSError(ENOENT)

        writepath(path, truncated)
        return 0

    def chmod(self, path):
        raise NotImplementedError('chown not implemented (never will be)')

    def chown(self, path):
        raise NotImplementedError('chown not implemented (never will be)')

    def statfs(self):
        return dict(f_bsize=512, f_blocks=0, f_bavail=2**63-1)
    
    def flush(self, path):
        # use telegram

        if path in self.buffers:
            writepath(path, self.buffers[path])
            del self.buffers[path]
        return 0
    
    def release(self, path):
        # Also upload the file when it's released, in case it wasn't flushed
        if path in self.buffers:
            writepath(path, self.buffers[path])
            del self.buffers[path]
        return 0

    def utimens(self, path, times=None):

        if times == None:
            times = (time.time(), time.time())
        if not (path in db[1] + ['/'] or path in db[0]):
            raise FuseOSError(ENOENT)
        db[2][path] = times
        savedb()

    def statfs(self, path):
        return dict(f_bsize=512, f_blocks=0, f_bavail=2**63-1)
    def flush(self, path, fh):
        # use telegram
        if path in self.buffers:
            writepath(path, self.buffers[path])
            del self.buffers[path]
        return 0
    def release(self, path, fh):
        # Also upload the file when it's released, in case it wasn't flushed
        if path in self.buffers:
            writepath(path, self.buffers[path])
            del self.buffers[path]
        return 0

def Mount(mountpoint, **kwargs) -> NoReturn:
    """
    Mounts the TelegramFUSE filesystem at the specified mountpoint.

    Args:
        mountpoint (str): The path where the filesystem will be mounted.
        **kwargs: Additional keyword arguments to be passed to the FUSE constructor.
        For example: foreground=True will run the filesystem in the foreground.

    Returns:
        None
    """
    FUSE(TelegramFUSE(), mountpoint, **kwargs)

if __name__ == '__main__':
    argparser = ArgumentParser()

    argparser.add_argument('--mount', type=str, help='Path to mountpoint', required=True)
    argparser.add_argument('--background', action='store_true', help='Run in background (daemon mode) (can\'t be used with --debug)')
    argparser.add_argument('--debug', action='store_true', help='Debug mode (can\'t be used with --background)')

    args = argparser.parse_args()

    if args.background and args.debug:
        argparser.error("--background and --debug can't be used at the same time")

    Mount(args.mount, foreground=not args.background, debug=args.debug)
