<?php

// Type alias (via class_alias or just use)
class Text extends Stringable {}
class IntVector extends ArrayObject {}

// Simple enum (PHP 8.1+)
enum Colour {
    case Red;
    case Green;
    case Blue;
}

// Class with nested class and nested enum
class Outer {
    public enum Status {
        case Active;
        case Inactive;
    }
    
    // Nested class (via inner class definition)
    public class InnerStruct {
        public string $name;
        public int $code;
    }
    
    // Method returning closure (nested function)
    public function getMultiplier(int $factor): Closure {
        $self = $this;
        // Nested function via closure
        return function(int $x) use ($self, $factor) {
            // Triple nested closure
            $innerHelper = function(int $a, int $b) {
                return $a * $b;
            };
            return $innerHelper($self->value + $x, $factor);
        };
    }
}

// Generic-like via docblocks (no true generics)
/** @template T */
class Box {
    /** @var T */
    public $content;
}

// Function with local class and nested enum
function functionWithLocalClass(): void {
    class LocalClass {
        public enum LocalEnum {
            case One;
            case Two;
        }
        
        public static function add(int $a, int $b): int {
            $inner = function() use ($a, $b) {
                return $a + $b;
            };
            return $inner();
        }
    }
    
    // Local alias (via class_alias)
    class_alias('LocalClass', 'LocalAlias');
}

// Variable definitions
$origin = new class { public int $x = 0; public int $y = 0; };
$bgColour = Colour::Blue;
$intBox = new Box(42);
$numbers = new IntVector([1, 2, 3]);

?>