import datetime, sys

class Log(object):
    """
    Simple log objects that write to and manage a designated file.
    """
    
    WARNING_INDICATOR =         "WARNING:"
    WIPE_MESSAGE =              "Fresh log"
    CLEAN_MESSAGE =             "Cleaning log"
    CLEAN_SUCCESS_MESSAGE =     "Log cleaned"
    CLEAN_CANCELLED_MESSAGE =   "Log already clean"
    """
    These are default messages that the log will use to mark the execution of a
    management function or prefix warning entries.
    """
    
    def __init__(self, file, max_lines=100, use_stdout=True):
        """
        Returns a new Log object that writes to the specified file. Optionally,
        a number of maximum log entires may be provided as well as whether or
        not to print all entries.
        """
        self.file = file
        self.max_lines = max_lines
        self.use_stdout = use_stdout
        self.wipe()

    def write(self, text, newline=True, warn=False):
        """
        Recieves text that will be logged in the designated file as well as
        printed to stdout. Setting warn to true will prefix the message with a
        warning indicator. Newline may be set to false if the text being logged
        will already end with a newline character.
        """
        assert type(text) is str
        message = str(datetime.datetime.now()) + " " 
        message += ((Log.WARNING_INDICATOR + " ") if warn else "")
        message += text
        message += ("\n" if newline else "")
        with open(self.file, "a") as file:
            file.write(message)
        if self.use_stdout:
            sys.stdout.write(message)
    
    def wipe(self):
        """
        Erases the log completely and leaves a single line in it noting that
        the wipe occurred.
        """
        with open(self.file, "w"):
            pass
        self.write(Log.WIPE_MESSAGE)
    
    def clean(self):
        """
        Reduce the number of lines in the log file to the value of max_lines if
        that number is being exceeded. If lines must be removed, deletion
        begins with the oldest entries first. A message noting the clean
        attempt will always be logged, followed by a message stating whether a
        cleaning occurred.
        """
        self.write(Log.CLEAN_MESSAGE)
        with open(self.file, "r") as file:
            lines = file.readlines()
        length = len(lines) + 1 #offset log entires created by this function
        if length > self.max_lines:
            with open(self.file, "w") as file:
                for line in lines[length - self.max_lines:]:
                    file.write(line)
            self.write(Log.CLEAN_SUCCESS_MESSAGE)
        else:
            self.write(Log.CLEAN_CANCELLED_MESSAGE)

"""
MIT License

Copyright (c) 2018 andynines

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""