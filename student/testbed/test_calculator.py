import pytest
from calculator import add, subtract

def test_add():
    assert add(2, 3) == 5, "add(2, 3) should return 5"

def test_subtract():
    assert subtract(5, 3) == 2, "subtract(5, 3) should return 2"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
