from enum import Enum
from typing import List, TypeVar, Callable

# Type alias
Text = str
IntVector = List[int]
T = TypeVar('T')

# Simple enum
class Colour(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

# Class with nested class, nested enum, nested function
class Outer:
    class Status(Enum):
        ACTIVE = 1
        INACTIVE = 2
    
    class InnerStruct:
        def __init__(self, name: str, code: int):
            self.name = name
            self.code = code
    
    # Nested function (method)
    def get_multiplier(self, factor: int) -> Callable[[int], int]:
        # Closure as nested function
        def multiplier(x: int) -> int:
            # Triple nested function
            def inner_helper(a: int, b: int) -> int:
                return a * b
            return inner_helper(self.value + x, factor)
        return multiplier

# Struct-like class
class Point:
    x: int
    y: int

# Generic/template class
class Box[T]:
    def __init__(self, content: T):
        self.content = content

# Free function with local class and nested function
def function_with_local_class():
    class LocalClass:
        class LocalEnum(Enum):
            ONE = 1
            TWO = 2
        
        @staticmethod
        def add(a: int, b: int) -> int:
            # Nested function inside method
            def inner():
                return a + b
            return inner()
    
    # Local type alias
    LocalAlias = int

# Variable definitions
origin = Point()
bg_colour = Colour.BLUE
int_box = Box(42)
numbers: IntVector = [1, 2, 3]