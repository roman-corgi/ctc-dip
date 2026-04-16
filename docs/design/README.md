# Abstract Design

There are two major design concepts:
1. Finite State Machine (FSM) that every channel implements. More accurately, every channel uses the same FSM implementation with their own instantiation guaranteeing identical behavior and no cross talk.
1. A conceptual data flow for an ideal channel. It is instructive to understand the ideal flow then add the limitations and customization's to the ideal for each channel later.

## Finite State Machine (FSM)

![FSM](../images/fsm.svg)

## Ideal Channel

![Ideal Channel](../images/abs_design.svg)
