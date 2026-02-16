import manimlib as ml


class SquareToCircle(ml.Scene):
    def construct(self):
        circle = ml.Circle()
        circle.set_fill(ml.BLUE, opacity=0.5)
        circle.set_stroke(ml.BLUE_E, width=4)
        square = ml.Square()

        self.play(ml.ShowCreation(square))
        self.wait()
        self.play(ml.ReplacementTransform(square, circle))
        self.wait()


class InteractiveDevelopment(ml.Scene):
    def construct(self):
        circle = ml.Circle()
        circle.set_fill(ml.BLUE, opacity=0.5)
        circle.set_stroke(ml.BLUE_E, width=4)
        square = ml.Square()

        self.play(ml.ShowCreation(square))
        self.wait()

        # This opens an iPython terminal where you can keep writing
        # lines as if they were part of this construct method.
        # In particular, 'square', 'circle' and 'self' will all be
        # part of the local namespace in that terminal.
        self.embed()

        # Try copying and pasting some of the lines below into
        # the interactive shell
        self.play(ml.ReplacementTransform(square, circle))
        self.wait()
        self.play(circle.animate.stretch(4, 0))
        self.play(ml.Rotate(circle, 90 * ml.DEGREES))
        self.play(circle.animate.shift(2 * ml.RIGHT).scale(0.25))

        text = ml.Text("""
            In general, using the interactive shell
            is very helpful when developing new scenes
        """)
        self.play(ml.Write(text))

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
        ml.always(circle.move_to, self.mouse_point)


class StackVisualization(ml.Scene):
    """
    Visualizes a program's call stack with function calls and local variables.
    Shows a simple program:

    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n-1)

    result = factorial(3)
    """

    def construct(self):
        # Title
        title = ml.Text("Call Stack Visualization", font_size=48)
        title.to_edge(ml.UP)
        self.play(ml.Write(title))
        self.wait()

        # Create code display on the left
        code_lines = [
            "def factorial(n):",
            "    if n <= 1:",
            "        return 1",
            "    return n * factorial(n-1)",
            "",
            "result = factorial(3)"
        ]

        code = ml.VGroup()
        for i, line in enumerate(code_lines):
            text_line = ml.Text(line, font="Monospace", font_size=24)
            text_line.align_to(ml.LEFT * 5, ml.LEFT)
            text_line.shift(ml.DOWN * 0.4 * i)
            code.add(text_line)

        code.to_edge(ml.LEFT, buff=0.5)
        code.shift(ml.UP * 0.5)

        self.play(ml.FadeIn(code))
        self.wait()

        # Stack pointer label
        stack_label = ml.Text("Stack →", font_size=36)
        stack_label.move_to(ml.RIGHT * 3 + ml.UP * 2.5)
        self.play(ml.Write(stack_label))

        # Base position for stack frames
        stack_base = ml.RIGHT * 3.5 + ml.DOWN * 2

        # Simulate the execution: factorial(3)
        self.wait(0.5)

        # Call factorial(3)
        frame1 = self.create_stack_frame("factorial(3)", ["n = 3"], stack_base)
        self.play(ml.FadeIn(frame1))
        self.wait(0.8)

        # Call factorial(2)
        frame2 = self.create_stack_frame("factorial(2)", ["n = 2"],
                                         stack_base + ml.UP * 1.5)
        self.play(ml.FadeIn(frame2))
        self.wait(0.8)

        # Call factorial(1)
        frame3 = self.create_stack_frame("factorial(1)", ["n = 1"],
                                         stack_base + ml.UP * 3.0)
        self.play(ml.FadeIn(frame3))
        self.wait(0.8)

        # Highlight the base case
        highlight = ml.SurroundingRectangle(frame3, color=ml.GREEN, buff=0.1)
        self.play(ml.ShowCreation(highlight))
        self.wait(0.5)

        # Return from factorial(1) - returns 1
        return_text1 = ml.Text("return 1", font_size=24, color=ml.GREEN)
        return_text1.next_to(frame3, ml.RIGHT)
        self.play(ml.Write(return_text1))
        self.wait(0.5)

        self.play(ml.FadeOut(highlight), ml.FadeOut(return_text1),
                  ml.FadeOut(frame3))
        self.wait(0.5)

        # Return from factorial(2) - returns 2 * 1 = 2
        return_text2 = ml.Text("return 2", font_size=24, color=ml.GREEN)
        return_text2.next_to(frame2, ml.RIGHT)
        self.play(ml.Write(return_text2))
        self.wait(0.5)
        self.play(ml.FadeOut(return_text2), ml.FadeOut(frame2))
        self.wait(0.5)

        # Return from factorial(3) - returns 3 * 2 = 6
        return_text3 = ml.Text("return 6", font_size=24, color=ml.GREEN)
        return_text3.next_to(frame1, ml.RIGHT)
        self.play(ml.Write(return_text3))
        self.wait(0.5)
        self.play(ml.FadeOut(return_text3), ml.FadeOut(frame1))
        self.wait(0.5)

        # Show final result
        result = ml.Text("result = 6", font_size=42, color=ml.YELLOW)
        result.move_to(ml.RIGHT * 3.5)
        self.play(ml.Write(result))
        self.wait(2)

    def create_stack_frame(self, function_name, variables, position):
        """Create a visual representation of a stack frame."""
        # Frame box
        frame = ml.VGroup()

        # Rectangle for the frame
        rect = ml.Rectangle(
            width=3,
            height=1.2,
            fill_color=ml.BLUE,
            fill_opacity=0.3,
            stroke_color=ml.BLUE_E,
            stroke_width=3
        )

        # Function name
        func_text = ml.Text(function_name, font_size=28)
        func_text.move_to(rect.get_top() + ml.DOWN * 0.3)

        # Variables
        var_texts = ml.VGroup()
        for i, var in enumerate(variables):
            var_text = ml.Text(var, font_size=22, color=ml.YELLOW)
            var_text.move_to(rect.get_center() + ml.DOWN * (0.15 + i * 0.3))
            var_texts.add(var_text)

        frame.add(rect, func_text, var_texts)
        frame.move_to(position)

        return frame
