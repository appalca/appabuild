import logging

logger = logging.getLogger("appabuild")
logger.setLevel(level=logging.DEBUG)

# Format the message in the logss
formatter = logging.Formatter(
    "{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)

# Write the logs in a file
file_handler = logging.FileHandler("appabuild.log", mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
