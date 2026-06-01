# Example Ruby file for testing extraction
class Greeter
  def initialize(name)
    @name = name
  end

  def say_hello
    puts "Hello, #{@name}!"
  end

  def self.greet_all(names)
    names.each { |n| puts "Hello, #{n}!" }
  end
end

module MathUtils
  def add(a, b)
    a + b
  end
end
