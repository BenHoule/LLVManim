import manim


class SquareToCircle(manim.Scene):
    def construct(self):
        circle = manim.Circle()
        circle.set_fill(manim.BLUE, opacity=0.5)
        circle.set_stroke(manim.BLUE_E, width=4)

        square = manim.Square()
        square.rotate(manim.PI / 4)

        self.play(manim.Create(square))  # animate the creation of the square
        self.wait()
        self.play(manim.Transform(square, circle))  # transform the square into the circle
        self.play(
            square.animate.set_fill(manim.RED, opacity=0.5)
        )  # animate the change of color


class InteractiveDevelopment(manim.Scene):
    def construct(self):
        circle = manim.Circle()
        circle.set_fill(manim.BLUE, opacity=0.5)
        circle.set_stroke(manim.BLUE_E, width=4)
        square = manim.Square()

        self.play(manim.Create(square))
        self.wait()

        # This opens an iPython terminal where you can keep writing
        # lines as if they were part of this construct method.
        # In particular, 'square', 'circle' and 'self' will all be
        # part of the local namespace in that terminal.
        self.embed()

        # Try copying and pasting some of the lines below into
        # the interactive shell
        self.play(manim.Transform(square, circle))
        self.wait()
        self.play(circle.animate.stretch(4, 0))
        self.play(manim.Rotate(circle, 90 * manim.DEGREES))
        self.play(circle.animate.shift(2 * manim.RIGHT).scale(0.25))

        text = manim.Text("""
            In general, using the interactive shell
            is very helpful when developing new scenes
        """)
        self.play(manim.Write(text))

        # In the interactive shell, you can just type
        # play, add, remove, clear, wait, save_state and restore,
        # instead of self.play, self.add, self.remove, etc.

        # To interact with the window, type touch().  You can then
        # scroll in the window, or zoom by holding down 'z' while scrolling,
        # and change camera perspective by holding down 'd' while moving
        # the mouse.  Press 'r' to reset to the standard camera position.
        # Press 'q' to stop interacting with the window and go back to
        # typing new commands into the shell.

        # In principle you can customize a scene to be responsive to
        # mouse and keyboard interactions
        manim.always(circle.move_to, self.mouse_point)
