The demo JSON fixtures record 123 UI states from the standalone HTML demos in commit
49c262e, before embedding them in the course shell. They cover both optimization modes,
all initialization choices, random initialization with Math.random fixed at 0.37,
parameter updates, back/reset, sample sizes, learning rates, batch sizes and speed controls.

`tests/browser/demo-scenarios.mjs` defines the interactions. The parity checks run the same
interactions inside each iframe and compare displayed results to these reference values.
The fixtures are reference observations, not values computed by a second implementation.
