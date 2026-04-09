#include <iostream>
#include <string>
#include <vector>

// Type aliases
using Text = std::string;
using IntVector = std::vector<int>;

// Simple enum
enum class Colour { Red, Green, Blue };

// Enum nested inside a class
class Outer {
public:
    enum class Status { Active, Inactive, Pending };
};

// Simple struct
struct Point {
    int x, y;
};

// Struct with nested enum and alias
struct Shape {
    enum class Type { Circle, Square, Triangle };
    using Coord = double;
    Coord centreX, centreY;
    Type type;
};

// Template struct
template <typename T>
struct Box {
    T content;
    Box(T val);
};

// Template class with nested enum and alias
template <typename T>
class Container {
public:
    enum class Operation { Add, Remove, Clear };
    using ValueType = T;
    
    Container();
    void add(T val);
    
    // Member function template
    template <typename U>
    void transform(U (*func)(T));
    
private:
    std::vector<T> data;
};

// Non-template class with nested struct and nested function (via local class)
class Wrapper {
private:
    int value;
    
public:
    Wrapper(int v);
    
    // Nested struct
    struct InnerStruct {
        std::string name;
        int code;
    };
    
    // Function returning a lambda (lambda acts as a nested function)
    auto getMultiplier(int factor);
    
    // Function containing a local class (which itself contains nested functions)
    void demonstrateLocalClass();
    
    // Static member with same name as Container::transform to test overloading/scoping
    static void transform(int x);
};

// Free function template declaration
template <typename T>
T maxValue(T a, T b);

// Non-template free function declaration
void printColour(Colour c);

// Variable declarations (definitions with initialisation)
extern Point origin;
extern Colour bgColour;
extern Outer::Status currentStatus;
extern Shape::Type shapeType;
extern Box<int> intBox;
extern Container<std::string> stringContainer;
extern IntVector numbers;
extern Text message;

// Old-style typedef aliases
typedef unsigned int uint;
typedef Colour PreferredColour;

// Nested template alias (C++11)
template <typename T>
using Vec = std::vector<T>;

// Function with a local class (nested function simulation) - declaration only
void functionWithLocalClass();

// ======================
// Definitions of variables (allocated storage)
// ======================
Point origin = {0, 0};
Colour bgColour = Colour::Blue;
Outer::Status currentStatus = Outer::Status::Active;
Shape::Type shapeType = Shape::Type::Circle;
Box<int> intBox(42);
Container<std::string> stringContainer;
IntVector numbers = {1, 2, 3, 4, 5};
Text message = "Hello, World!";

// ======================
// Function definitions (bodies are empty or trivial for parsing testing)
// ======================

template <typename T>
Box<T>::Box(T val) : content(val) {}

template <typename T>
Container<T>::Container() {}

template <typename T>
void Container<T>::add(T val) {}

template <typename T>
template <typename U>
void Container<T>::transform(U (*func)(T)) {}

Wrapper::Wrapper(int v) : value(v) {}

auto Wrapper::getMultiplier(int factor) {
    // Lambda as a nested function
    return [this, factor](int x) -> int {
        // Inner lambda nested inside another lambda
        auto innerHelper = [](int a, int b) { return a * b; };
        return innerHelper(this->value + x, factor);
    };
}

void Wrapper::demonstrateLocalClass() {
    // Local class (only visible inside this function)
    class LocalClass {
    public:
        static int add(int a, int b);
        
        // Nested function inside local class
        void printSum(int a, int b);
    };
    
    // The local class can be instantiated here, but we omit statements
    // (LocalClass obj;)
}

// Free function template definition
template <typename T>
T maxValue(T a, T b) {
    // Empty body for parsing testing
}

// Non-template free function definition
void printColour(Colour c) {
    // Empty body
}

// Function with a local class
void functionWithLocalClass() {
    class Local {
    public:
        enum class LocalEnum { One, Two };
        struct LocalStruct { int x; };
        static void nestedFunction();
    };
    
    // Local aliases inside function
    using LocalAlias = int;
    typedef double LocalTypedef;
    
    // We can declare variables, but no statements (for parsing focus)
    LocalAlias a;
    LocalTypedef b;
}

// Static member definition
void Wrapper::transform(int x) {
    // Another transform implementation
}

// Static member of local class defined outside (though unusual, it's legal if Local had static members)
// Not defined here to keep focus on parsing.