try:
    from wxmeow import logger
except:
    pass
import glob
import os
import shutil
import time
import wxjson_noaa as wx

ext = ".pkl"

files = sorted(glob.glob("../*"+ext))
now = time.time()

for f in files:

    loc = f.split("/")[1].split(".")[0]

    if now - os.path.getatime(f) > 600:

        logger.info(f"refreshing {loc}")
        meow = wx.meowcast(loc)
        shutil.move(f.split("/")[1], f)

