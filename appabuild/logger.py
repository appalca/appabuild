import logging
import sys
from typing import Tuple

from pydantic import ValidationError

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)

# Format the message in the logs
formatter = logging.Formatter(
    "{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
)

# Write the logs in a file
file_handler = logging.FileHandler("appabuild.log", mode="w", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Redirect all the logs to stdout
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)


def loc_to_str(loc: Tuple[int | str, ...]) -> str:
    """
    Transform a loc path from an ErrorDetails (pydantic) into a human-readable path.
    """
    result = loc[0]
    for elem in loc[1:]:
        if type(elem) is int:
            result += "[" + str(elem) + "]"
        else:
            result += "->" + elem
    return result


def log_validation_error(e: ValidationError):
    """
    Write a ValidationError (pydantic) in the logs.
    """
    for error in e.errors():
        match error["type"]:
            case "missing":
                logger.error("Missing field %s", loc_to_str(error["loc"]))
            case "value_error":
                logger.error(error["msg"])
            case "key_error":
                loc = error["loc"] + (error["ctx"]["field"],)
                logger.error("Missing field %s", loc_to_str(loc))
            case "parameter_type":
                logger.error(
                    "The field %s can't be of type %s, only of types: [%s]",
                    loc_to_str(error["loc"]),
                    error["ctx"]["wrong_type"],
                    ", ".join(error["ctx"]["allowed_types"]),
                )
            case "enum_default_value":
                logger.error(
                    "The enum type parameter %s must have a default value that is one of its weights",
                    loc_to_str(error["loc"]),
                )
            case "string_type":
                logger.error(
                    "The field %s must be a valid string (non empty)",
                    loc_to_str(error["loc"]),
                )
            case "list_type":
                logger.error(
                    "The field %s must be a valid list (non empty)",
                    loc_to_str(error["loc"]),
                )
            case "reserved_name":
                logger.error(
                    "The name %s is a reserved name (location: %s)",
                    error["ctx"]["name"],
                    loc_to_str(error["loc"]),
                )
            case _:
                logger.error(error["msg"])
