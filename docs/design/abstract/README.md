---
title: Abstract
parent: Design
---

# Abstract Design

There are two major design concepts:
1. Finite State Machine (FSM) that every channel implements. More accurately, every channel uses the same FSM implementation with their own instantiation guaranteeing identical behavior and no cross talk.
1. A conceptual data flow for an ideal channel. It is instructive to understand the ideal flow then add the limitations and customization's to the ideal for each channel later.

## Finite State Machine (FSM)

![FSM](/ctc-dip/assets/images/fsm.svg){: width="10%"}

| State | Explaination |
| :---: | :--- |
| Construction	| Create a workspace for shared content and specifically written information to avoid file lock issues with multiple processes accessing the same file at the same time. To conserve working space, Product data is not copied because two Delegations should not be transmuting the same products at the same time. |
| Delegation | Delegate a sandbox to a worker (DRP for all level Transmutations) in a sandbox. Wait for the worker to complete and transition to the next state depending on the what results are found. |
| General Quarters | Secure the log information. Review failure condition and attempt a recovery if possible. In all circumstances, generate a report and add it as an entry to the operational logs. Include if a recovery was attempted or not and what the recovery attempt was. |
| Panic | Secure the log information. Generate a report sending it as a flare – to everyone – and record it as an entry in the operational logs. |
| Sanitization | Remove the workspace. |
| Warehouse | Move any products in the workspace to the archival location. |

## Ideal Channel

![Ideal Channel](/ctc-dip/assets/images/abs_design.svg)
