# svc:widget
aka:         widget, the widget service
state:       stable
owns:        widget/serve.py, widget/config.py
depends:     -
dependents:  -
invariants:  config must be loaded before serve starts
open:        -
verified:    2026-09-01
run:         python widget/serve.py
