# Data Model
```
RenderStep
├── action: ActionKind        (what happened)
├── event: IREvent            (the IR event that caused it)
└── state: FrameStackView     (the full stack state AFTER this step)
      └── frames: list[StackFrameView]
            ├── function_name: str
            └── slots: list[StackSlotView]
                  └── name: str
```
