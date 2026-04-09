-- No type aliases natively (can be simulated with variables)
Text = "string"

-- No enums natively, use tables
Colour = { RED = 1, GREEN = 2, BLUE = 3 }

-- Table with nested table (simulating class/struct)
Outer = {
    Status = { ACTIVE = 1, INACTIVE = 2 },
    InnerStruct = { name = "", code = 0 }
}

-- Metatable for OOP (simulating class)
Point = { x = 0, y = 0 }
Point.__index = Point

function Point:new(x, y)
    local obj = { x = x or 0, y = y or 0 }
    setmetatable(obj, self)
    return obj
end

-- Generic "template" via function
function Box(content)
    return { content = content }
end

-- Function with nested function and local table (nested "class")
function functionWithLocalClass()
    -- Local table as class
    local LocalClass = {}
    LocalClass.LocalEnum = { ONE = 1, TWO = 2 }
    
    function LocalClass:add(a, b)
        -- Triple nested function
        local function innerHelper(x, y)
            return x + y
        end
        return innerHelper(a, b)
    end
    
    -- Local alias (via assignment)
    local LocalAlias = "string"
end

-- Function returning closure (nested function)
function Wrapper(value)
    return {
        value = value,
        getMultiplier = function(self, factor)
            return function(x)
                local function innerHelper(a, b)
                    return a * b
                end
                return innerHelper(self.value + x, factor)
            end
        end
    }
end

-- Variable definitions
local origin = Point:new(0, 0)
local bgColour = Colour.BLUE
local intBox = Box(42)
local numbers = { 1, 2, 3 }