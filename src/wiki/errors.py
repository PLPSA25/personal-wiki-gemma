"""Expected, user-facing problems. The CLI prints their message and exits without a stack trace."""


class WikiError(Exception):
    """Base class for problems the user can fix (bad path, model not running, empty index...)."""


class SourceError(WikiError):
    """A source file cannot be read safely or is not a supported type."""


class ModelError(WikiError):
    """The local language model cannot be used (server down, model missing, timeout, bad reply)."""
