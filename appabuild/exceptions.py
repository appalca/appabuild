class BwDatabaseError(Exception):
    """Raised when any problem concerning the data (Database, Exchanges, Activities) is
    encountered."""

    pass


class BwMethodError(Exception):
    """Raised when any problem concerning the methods is encountered."""

    pass


class SerializedDataError(Exception):
    """Raised when any problem concerning yaml/json dataset is encountered."""

    pass
