import random
import string
import sys
from typing import Dict, Any

def generate_random_string(length: int = 10) -> str:
    """Generates a random string with mixed ASCII characters"""
    letters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(letters) for _ in range(length))

def generate_complex_payload() -> Dict[str, Any]:
    """
    Generates a nasty JSON payload to test data fidelity.
    Includes: Unicode, Large Ints, Nested Dicts, Nulls.
    """
    return {
        "user_info": {
            "name": "בדיקה ארז 🚀",  # Hebrew + Emoji (Unicode test)
            "id": "user_" + generate_random_string(5),
            "bio": "Line1\nLine2\tTabbed",  # Special whitespace characters
        },
        "metrics": {
            "login_count": sys.maxsize + 1,  # Super large integer (Python handles it, JSON spec validates it)
            "session_duration": 45.56789123, # Float precision
            "is_active": True
        },
        "metadata": {
            "tags": ["admin", "null_test", None],  # List with Null
            "nested_level_1": {
                "nested_level_2": {
                    "secret_code": generate_random_string(20)
                }
            }
        },
        "edge_cases": {
            "empty_string": "",
            "zero": 0,
            "false_val": False
        }
    }