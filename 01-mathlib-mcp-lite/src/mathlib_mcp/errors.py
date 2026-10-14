"""Errors an agent can read and act on."""


class ToolError(Exception):
    def __init__(self, error_code: str, message: str, fix_hint: str) -> None:
        self.error_code = error_code
        self.message = message
        self.fix_hint = fix_hint
        super().__init__(message)

    def to_dict(self) -> dict[str, str]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "fix_hint": self.fix_hint,
        }
