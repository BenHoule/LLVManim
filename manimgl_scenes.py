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
    """Visualize load -> use -> store with stack state present at start."""

    def construct(self):
        ir_lines = [
            "define i32 @dummy(i32 %x) {",
            "entry:",
            "  %x.addr = alloca i32, align 4",
            "  %y.addr = alloca i32, align 4",
            "  store i32 %x, ptr %x.addr, align 4",
            "  store i32 0, ptr %y.addr, align 4",
            "  %v = load i32, ptr %x.addr, align 4",
            "  %sum = add i32 %v, 1",
            "  store i32 %sum, ptr %y.addr, align 4",
            "  ret i32 %sum",
            "}",
        ]

        ir_group = ml.VGroup()
        for i, line in enumerate(ir_lines):
            txt = ml.Text(line, font="Monospace", font_size=22)
            txt.align_to(ml.LEFT * 6.3, ml.LEFT)
            txt.shift(ml.DOWN * 0.40 * i)
            ir_group.add(txt)

        ir_group.to_edge(ml.LEFT, buff=0.45)
        ir_group.shift(ml.UP * 1.2)

        slot_width = 4.1
        slot_height = 0.72
        stack_top = ml.RIGHT * 3.7 + ml.UP * 1.85

        def make_slot(label, fill_color, y_shift):
            rect = ml.Rectangle(
                width=slot_width,
                height=slot_height,
                fill_color=fill_color,
                fill_opacity=0.25,
                stroke_color=fill_color,
                stroke_width=2,
            )
            rect.move_to(stack_top + ml.DOWN * y_shift)
            text = ml.Text(label, font="Monospace", font_size=22)
            text.move_to(rect.get_center())
            return ml.VGroup(rect, text)

        return_addr = make_slot("[rbp+8]  return address", ml.BLUE_D, 0.00)
        saved_rbp = make_slot("[rbp+0]  saved rbp", ml.TEAL_D, 0.84)
        local_x = make_slot("[rbp-4]  x.addr = 42", ml.GREEN_D, 1.68)
        local_y = make_slot("[rbp-8]  y.addr = 0", ml.MAROON_D, 2.52)
        padding = make_slot("[rbp-16..rbp-9]  padding", ml.GREY_BROWN, 3.36)

        stack_slots = ml.VGroup(
            return_addr,
            saved_rbp,
            local_x,
            local_y,
            padding,
        )
        stack_outline = ml.SurroundingRectangle(
            stack_slots,
            color=ml.WHITE,
            buff=0.08,
        )

        rbp_label = ml.Text("RBP", font_size=21, color=ml.TEAL_A)
        rbp_label.next_to(saved_rbp[0], ml.LEFT, buff=0.25)
        rbp_arrow = ml.Arrow(
            rbp_label.get_right(),
            saved_rbp[0].get_left() + ml.RIGHT * 0.05,
            buff=0.05,
            color=ml.TEAL_A,
            stroke_width=4,
        )

        rsp_label = ml.Text("RSP", font_size=21, color=ml.PURPLE_A)
        rsp_label.next_to(padding[0], ml.LEFT, buff=0.25)
        rsp_arrow = ml.Arrow(
            rsp_label.get_right(),
            padding[0].get_left() + ml.RIGHT * 0.05,
            buff=0.05,
            color=ml.PURPLE_A,
            stroke_width=4,
        )

        stack_group = ml.VGroup(
            stack_slots,
            stack_outline,
            rbp_label,
            rbp_arrow,
            rsp_label,
            rsp_arrow,
        )

        self.add(ir_group, stack_group)
        self.wait(0.5)

        load_line = ir_group[6]
        add_line = ir_group[7]
        store_line = ir_group[8]

        line_box = ml.SurroundingRectangle(
            load_line,
            color=ml.YELLOW,
            buff=0.07,
        )
        self.play(ml.ShowCreation(line_box))

        load_mem_box = ml.SurroundingRectangle(
            local_x,
            color=ml.YELLOW,
            buff=0.06,
        )
        self.play(ml.ShowCreation(load_mem_box))

        v_box = ml.RoundedRectangle(
            width=2.1,
            height=0.9,
            corner_radius=0.15,
            fill_color=ml.YELLOW,
            fill_opacity=0.2,
            stroke_color=ml.YELLOW,
            stroke_width=3,
        )
        v_box.move_to(ml.RIGHT * 0.2 + ml.DOWN * 2.0)
        v_text = ml.Text(
            "%v = 42",
            font="Monospace",
            font_size=28,
            color=ml.YELLOW,
        )
        v_text.move_to(v_box.get_center())
        v_group = ml.VGroup(v_box, v_text)

        load_arrow = ml.Arrow(
            local_x[0].get_left() + ml.LEFT * 0.15,
            v_box.get_right() + ml.RIGHT * 0.05,
            buff=0.1,
            color=ml.YELLOW,
            stroke_width=5,
        )
        self.play(
            ml.ShowCreation(load_arrow),
            ml.FadeIn(v_group, shift=ml.UP * 0.15),
        )

        self.play(
            ml.Transform(
                line_box,
                ml.SurroundingRectangle(add_line, color=ml.ORANGE, buff=0.07),
            ),
            ml.FadeOut(load_mem_box),
        )

        sum_box = ml.RoundedRectangle(
            width=2.6,
            height=0.9,
            corner_radius=0.15,
            fill_color=ml.ORANGE,
            fill_opacity=0.2,
            stroke_color=ml.ORANGE,
            stroke_width=3,
        )
        sum_box.next_to(v_box, ml.DOWN, buff=0.35)
        sum_text = ml.Text(
            "%sum = 43",
            font="Monospace",
            font_size=28,
            color=ml.ORANGE,
        )
        sum_text.move_to(sum_box.get_center())
        sum_group = ml.VGroup(sum_box, sum_text)

        add_arrow = ml.Arrow(
            v_box.get_bottom() + ml.DOWN * 0.05,
            sum_box.get_top() + ml.UP * 0.05,
            buff=0.1,
            color=ml.ORANGE,
            stroke_width=5,
        )
        self.play(
            ml.ShowCreation(add_arrow),
            ml.FadeIn(sum_group, shift=ml.UP * 0.1),
        )

        self.play(
            ml.Transform(
                line_box,
                ml.SurroundingRectangle(
                    store_line,
                    color=ml.MAROON_B,
                    buff=0.07,
                ),
            )
        )

        store_mem_box = ml.SurroundingRectangle(
            local_y,
            color=ml.MAROON_B,
            buff=0.06,
        )
        store_arrow = ml.Arrow(
            sum_box.get_right() + ml.RIGHT * 0.05,
            local_y[0].get_left() + ml.LEFT * 0.1,
            buff=0.1,
            color=ml.MAROON_B,
            stroke_width=5,
        )

        new_y_text = ml.Text(
            "[rbp-8]  y.addr = 43",
            font="Monospace",
            font_size=22,
        )
        new_y_text.move_to(local_y[1].get_center())

        self.play(ml.ShowCreation(store_mem_box), ml.ShowCreation(store_arrow))
        self.play(ml.Transform(local_y[1], new_y_text))
        self.wait(1.8)


