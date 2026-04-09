// Type aliases
type Text = String;
type IntVector = Vec<i32>;

// Simple enum
enum Colour {
    Red,
    Green,
    Blue,
}

// Struct with nested struct
struct Outer {
    value: i32,
    inner: InnerStruct,
}

struct InnerStruct {
    name: String,
    code: i32,
}

// Struct with nested enum
struct Shape {
    centre_x: f64,
    centre_y: f64,
    shape_type: ShapeType,
}

enum ShapeType {
    Circle,
    Square,
    Triangle,
}

// Generic struct (template)
struct Box<T> {
    content: T,
}

// Struct with nested function via field (function pointer)
struct Wrapper {
    value: i32,
    get_multiplier: fn(i32, i32) -> i32,
}

// Function with nested function and local struct
fn function_with_local_class() {
    // Local struct
    struct LocalStruct {
        x: i32,
    }
    
    // Local enum
    enum LocalEnum {
        One,
        Two,
    }
    
    // Local type alias
    type LocalAlias = i32;
    
    // Nested function (Rust allows this!)
    fn nested_function(a: i32, b: i32) -> i32 {
        // Triple nested function
        fn inner_helper(x: i32, y: i32) -> i32 {
            x + y
        }
        inner_helper(a, b)
    }
    
    // Closure (also nested)
    let closure = |x: i32| -> i32 {
        let inner = |a: i32, b: i32| a * b;
        inner(x, 2)
    };
    
    let _ = closure(5);
}

// Function returning closure (nested function)
fn wrapper_get_multiplier(value: i32, factor: i32) -> impl Fn(i32) -> i32 {
    move |x: i32| {
        // Nested function inside closure
        fn inner_helper(a: i32, b: i32) -> i32 {
            a * b
        }
        inner_helper(value + x, factor)
    }
}

// Variable definitions
static ORIGIN: (i32, i32) = (0, 0);
static mut BG_COLOUR: Colour = Colour::Blue;
static INT_BOX: Box<i32> = Box { content: 42 };
static NUMBERS: IntVector = vec![1, 2, 3];

fn main() {
    // Variables can be declared here, but no statements per request
}