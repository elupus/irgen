class IrgenError(Exception):
    """Base class for IR generator exceptions."""

class IrgenInputError(IrgenError):
    """Raised when the input data is invalid."""
