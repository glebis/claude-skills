import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from granola import extract_people


def test_extract_people_returns_names_and_emails_from_nested_attendees():
    # Arrange
    doc = {
        "people": {
            "attendees": [
                {
                    "details": {
                        "person": {
                            "name": {
                                "fullName": "Alice Johnson"
                            }
                        }
                    },
                    "email": "alice@example.com"
                },
                {
                    "details": {
                        "person": {
                            "name": {
                                "fullName": "Bob Smith"
                            }
                        }
                    },
                    "email": "bob@example.com"
                }
            ]
        }
    }

    # Act
    result = extract_people(doc)

    # Assert
    assert result == [
        {"name": "Alice Johnson", "email": "alice@example.com"},
        {"name": "Bob Smith", "email": "bob@example.com"}
    ]
