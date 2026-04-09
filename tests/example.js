// Type alias (via JSDoc or just variable)
/** @typedef {string} Text */
/** @typedef {number[]} IntVector */

// No enums natively, but Object.freeze as workaround
const Colour = Object.freeze({
    RED: 1,
    GREEN: 2,
    BLUE: 3
});

// Class with nested class (via static property)
class Outer {
    static Status = Object.freeze({
        ACTIVE: 1,
        INACTIVE: 2
    });
    
    // Nested class via static property
    static InnerStruct = class {
        constructor(name, code) {
            this.name = name;
            this.code = code;
        }
    };
    
    constructor(value) {
        this.value = value;
    }
    
    // Method returning nested function
    getMultiplier(factor) {
        const self = this;
        // Nested function
        return function(x) {
            // Triple nested function
            function innerHelper(a, b) {
                return a * b;
            }
            return innerHelper(self.value + x, factor);
        };
    }
}

// Function with local class
function functionWithLocalClass() {
    class LocalClass {
        static LocalEnum = Object.freeze({ ONE: 1, TWO: 2 });
        static add(a, b) {
            const inner = () => a + b;
            return inner();
        }
    }
    
    // Local alias
    const LocalAlias = Number;
}

// Variable definitions
const origin = { x: 0, y: 0 };
let bgColour = Colour.BLUE;
const intBox = { content: 42 };
const numbers = [1, 2, 3];