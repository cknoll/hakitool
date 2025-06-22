
import logging
import re
import time

# source:
class NoColorFormatter(logging.Formatter):
    """
    Log formatter that strips terminal colour
    escape codes from the log message.
    """

    # Regex for ANSI colour codes
    ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

    def format(self, record):
        """Return logger message with terminal escapes removed."""
        res =  " ".join((
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            record.name,
            re.sub(self.ANSI_RE, "", record.levelname),
            re.sub(self.ANSI_RE, "", record.getMessage()),
        ))

        return res
