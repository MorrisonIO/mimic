import datetime
import os, os.path
import platform


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(os.path.abspath(os.path.join(BASE_DIR, os.pardir)), 'media/uploads/')


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

for filename in os.listdir(TARGET_DIR):
    # print(creation_date('in/'+ filename))
    fileTime = datetime.datetime.fromtimestamp(int(creation_date(TARGET_DIR + filename)))
    expaerTime = datetime.datetime.today() - datetime.timedelta(weeks=12)
    if fileTime < expaerTime:
        os.remove(TARGET_DIR + filename)
