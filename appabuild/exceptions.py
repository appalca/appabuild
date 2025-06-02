class BwDatabaseError(Exception):
    """Raised when any problem concerning the data (Database, Exchanges, Activities) is
    encountered."""

    def __init__(self, *args, exception_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.exception_type = exception_type


class BwMethodError(Exception):
    """Raised when any problem concerning the methods is encountered."""

    pass


class SerializedDataError(Exception):
    """Raised when any problem concerning yaml/json dataset is encountered."""

    pass
