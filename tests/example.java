import java.util.List;
import java.util.ArrayList;
import java.util.function.Function;
import java.util.function.IntBinaryOperator;

// Type aliases (not directly supported, use extends/implements)
class Text extends String {}
class IntVector extends ArrayList<Integer> {}

// Simple enum
enum Colour {
    RED, GREEN, BLUE
}

// Class with nested class, nested enum
class Outer {
    public enum Status {
        ACTIVE, INACTIVE
    }
    
    // Nested static class (simulating struct)
    public static class InnerStruct {
        public String name;
        public int code;
    }
    
    private int value;
    
    Outer(int value) {
        this.value = value;
    }
    
    // Method returning lambda (workaround for nested function)
    public Function<Integer, Integer> getMultiplier(int factor) {
        // Lambda as nested function
        return (Integer x) -> {
            // Nested lambda inside lambda
            IntBinaryOperator innerHelper = (a, b) -> a * b;
            return innerHelper.applyAsInt(this.value + x, factor);
        };
    }
}

// Generic class (template)
class Box<T> {
    T content;
    Box(T content) { this.content = content; }
}

// Record (struct-like, Java 14+)
record Point(int x, int y) {}

// Function with local class (but no local functions)
public class Main {
    static void functionWithLocalClass() {
        // Local class
        class LocalClass {
            enum LocalEnum { ONE, TWO }
            
            static int add(int a, int b) {
                // Local class can't have lambdas that capture effectively final only
                IntBinaryOperator inner = (x, y) -> x + y;
                return inner.applyAsInt(a, b);
            }
        }
        
        // No local type aliases in Java
    }
    
    // Variable definitions
    static Point origin = new Point(0, 0);
    static Colour bgColour = Colour.BLUE;
    static Box<Integer> intBox = new Box<>(42);
    static List<Integer> numbers = List.of(1, 2, 3);
}