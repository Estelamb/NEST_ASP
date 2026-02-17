NEST Simulation
===============

This module provides a Python-based simulation environment that replicates the behavior of multiple NEST nodes. It allows for scalability testing and validation of the system's logic in parallel with physical hardware.

Operational Logic
-----------------

The simulation runs a **Finite State Machine (FSM)** that mimics the life cycle of a poultry nest. The system transitions through states based on random persistence and environmental conditions.

* **WAITING_FOR_HEN**: Idle state with no weight or UID detected.
* **HEN_INSIDE**: Simulates hen entry with random weight (2000g-3500g) and a specific UID.
* **EGGS_DEPOSITED**: Represents the hen leaving while the weight of the eggs remains.
* **PERSON_COLLECTING**: Authorized user (Farmer) collecting production, identified by a unique UID.

Code Documentation
------------------

.. automodule:: nest_sim
   :members: