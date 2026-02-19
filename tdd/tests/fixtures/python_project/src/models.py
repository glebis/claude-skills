from dataclasses import dataclass


@dataclass
class User:
    """Represents a user in the system."""

    name: str
    email: str

    def validate_email(self) -> bool:
        """Check if email contains @ symbol."""
        return "@" in self.email
