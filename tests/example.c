#include <stdint.h>

// Type alias
typedef char* Text;
typedef struct IntVector { int* data; int size; } IntVector;

// Simple enum
enum Colour { COLOUR_RED, COLOUR_GREEN, COLOUR_BLUE };

// Struct with nested struct
struct Outer {
    enum Status { STATUS_ACTIVE, STATUS_INACTIVE };
    struct InnerStruct {
        char* name;
        int code;
    } inner;
};

// Struct with nested enum
struct Shape {
    enum Type { TYPE_CIRCLE, TYPE_SQUARE, TYPE_TRIANGLE };
    double centreX, centreY;
    enum Type type;
};

// Template-like via macro (not real template, but nested possible)
#define BOX(T) struct Box_##T { T content; }

BOX(int);
BOX(double);

// Struct with nested function pointer (simulating nested function)
struct Wrapper {
    int value;
    // Function pointer as "nested function"
    int (*get_multiplier)(struct Wrapper*, int);
};

// Free function with local struct (local type)
void function_with_local_struct(void) {
    struct LocalStruct {
        enum LocalEnum { LOCAL_ONE, LOCAL_TWO };
        int x;
    };
    typedef int LocalAlias;
}

// Variable definitions
struct Point { int x, y; } origin = {0, 0};
enum Colour bgColour = COLOUR_BLUE;
struct Outer currentStatus;
struct Shape shapeType;
BOX(int) intBox = {42};