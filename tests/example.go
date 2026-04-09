package main

// Type alias
type Text string
type IntVector []int

// Simple enum (using iota)
type Colour int
const (
    ColourRed Colour = iota
    ColourGreen
    ColourBlue
)

// Struct with nested struct
type Outer struct {
    Value int
    Inner struct {
        Name string
        Code int
    }
}

// Nested enum inside struct (via constants)
type Shape struct {
    CentreX, CentreY float64
    Type ShapeType
}

type ShapeType int
const (
    TypeCircle ShapeType = iota
    TypeSquare
    TypeTriangle
)

// Generic struct (Go 1.18+)
type Box[T any] struct {
    Content T
}

// Struct with nested function field
type Wrapper struct {
    value int
    // Function field (can hold closure)
    GetMultiplier func(factor int) func(int) int
}

// Free function with nested function
func functionWithLocalClass() {
    // Local struct definition
    type LocalStruct struct {
        X int
        // Nested enum inside local struct
        LocalEnum int
    }
    
    // Local type alias
    type LocalAlias = int
    
    // Nested function inside function
    nestedFunc := func(a, b int) int {
        // Triple nested function
        innerHelper := func(x, y int) int {
            return x + y
        }
        return innerHelper(a, b)
    }
    _ = nestedFunc
}

// Method that returns nested function
func (w *Wrapper) GetMultiplierMethod(factor int) func(int) int {
    return func(x int) int {
        innerHelper := func(a, b int) int {
            return a * b
        }
        return innerHelper(w.value + x, factor)
    }
}

// Variable definitions
var origin = struct{ X, Y int }{0, 0}
var bgColour = ColourBlue
var intBox = Box[int]{Content: 42}
var numbers = IntVector{1, 2, 3}