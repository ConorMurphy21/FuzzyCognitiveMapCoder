import os
from shutil import copyfile


class TempFileManager:

    def __init__(self, location, name):
        self.og_path = location + name
        self.path = location + "temp" + name
        copyfile(self.og_path, self.path)

    # deletes the temporary file
    def close(self):
        os.remove(self.path)
