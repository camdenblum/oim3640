
import turtle 

def draw_square(turtle_obj, size =100):
    """Draw a square with a given size"""
    for _ in range(4):
            turtle_obj.forward(size)
            turtle.obj.left(90)
    
def main():
        t=turtle.Turtle
        t.speed(5)
        draw_square(5)
        draw_square(t)
        draw_square(t,size=50)
        turtle.mainloop()

def draw_spiral(t):
      """draw one square turn a angle then draw another square and repeat"""
      for i in range(36):
        draw_square(t, 50)
        t.left(10)

if __name__ == "__main__":
    main()




