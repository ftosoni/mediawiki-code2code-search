// Type aliases
type Text = string;
type IntVector = number[];
type Colour = 'red' | 'green' | 'blue';  // Union type as enum substitute

// Enum
enum StatusEnum {
    Active,
    Inactive,
    Pending
}

// Namespace for grouping (substitute for unsupported nested classes/enums in TS classes)
namespace Outer {
    export enum Status {
        Active,
        Inactive
    }
    
    export class InnerStruct {
        constructor(public name: string, public code: number) {}
    }
    
    export interface InnerInterface {
        id: number;
    }
}

class OuterClass {
    private value: number;
    
    constructor(value: number) {
        this.value = value;
    }
    
    getMultiplier(factor: number): (x: number) => number {
        const self = this;
        return function(x: number): number {
            function innerHelper(a: number, b: number): number {
                return a * b;
            }
            return innerHelper(self.value + x, factor);
        };
    }
}

// Generic class (template)
class Box<T> {
    constructor(public content: T) {}
}

// Struct-like interface
interface Point {
    x: number;
    y: number;
}

// Function with local class, local interface, local type alias
function functionWithLocalClass(): void {
    class LocalClass {
        add(a: number, b: number): number {
            const inner = (): number => a + b;
            return inner();
        }
    }
    
    interface LocalInterface {
        field: string;
    }
    
    type LocalAlias = number;
}

// Variable definitions
const origin: Point = { x: 0, y: 0 };
let bgColour: Colour = 'blue';
const intBox = new Box<number>(42);
const numbers: IntVector = [1, 2, 3];