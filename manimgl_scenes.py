import manimlib


class SquareToCircle(manimlib.Scene):
    def construct(self):
        circle = manimlib.Circle()
        circle.set_fill(manimlib.BLUE, opacity=0.5)
        circle.set_stroke(manimlib.BLUE_E, width=4)
        square = manimlib.Square()

        self.play(manimlib.ShowCreation(square))
        self.wait()
        self.play(manimlib.ReplacementTransform(square, circle))
        self.wait()


class InteractiveDevelopment(manimlib. Scene):
    def construct(self):
        circle = manimlib.Circle()
        circle.set_fill(manimlib.BLUE, opacity=0.5)
        circle.set_stroke(manimlib.BLUE_E, width=4)
        square = manimlib.Square()

        self.play(manimlib.ShowCreation(square))
        self.wait()

        # This opens an iPython terminal where you can keep writing
        # lines as if they were part of this construct method.
        # In particular, 'square', 'circle' and 'self' will all be
        # part of the local namespace in that terminal.
        self.embed()

        # Try copying and pasting some of the lines below into
        # the interactive shell
        self.play(manimlib.ReplacementTransform(square, circle))
        self.wait()
        self.play(circle.animate.stretch(4, 0))
        self.play(manimlib.Rotate(circle, 90 * manimlib.DEGREES))
        self.play(circle.animate.shift(2 * manimlib.RIGHT).scale(0.25))

        text = manimlib.Text("""
            In general, using the interactive shell
            is very helpful when developing new scenes
        """)
        self.play(manimlib.Write(text))

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
        manimlib.always(circle.move_to, self.mouse_point)
