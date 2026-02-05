for i in range(1, 4):
    print("Iteration:", i)
    print("Square:", i * i)
    print()

for i in range(1, 6, 2):
    print(i)

#name = "ABCDEFGHIJK"

#name[0]

#name[1, 5, 2]

a = 5
b = a
a = 10
print(b)
print(a)

a = [1, 2, 3] #list is mutable 
b = a.append(4)
print(b)
print(a)

x = 10 

def foo():
    message = "hello"
    x = 5
    return x

#print(foo())
#print()
#print(message)

#dray a trinagle 

def triangle(s, height):
    for i in range(1, height + 1):
        print(s * i)

triangle("+", 4)

#def square(s, width, height):
 #   for i in range(height):
#        print(s * width)

#square("O", 4, 4)

def backwards_triangle(size):
    for i in range(size):
        print(" " * (size - i -1) + "#" * (i+1))

backwards_triangle(5)






