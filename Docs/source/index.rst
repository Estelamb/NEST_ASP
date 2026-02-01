Welcome to NEST's Documentation
========================================

Welcome to the documentation of the NEST project. This document provides a comprehensive guide to understanding, using, and developing a technical solution for the automated management of poultry farms.

In this documentation, you will find detailed explanations of the system's architecture, which focuses on egg quality monitoring and protection. It covers the integration of physical hardware with IoT service platforms and the use of edge computing to ensure low-latency responses.

Whether you are a developer, agricultural engineer, or farm manager, this documentation aims to serve as a valuable resource for understanding and extending the capabilities of the Next-generation Edge System for Tracking (NEST).

What is NEST?
-------------

NEST (Next-generation Edge System for Tracking) is an innovative project developed to solve real-world challenges in smart farming. The system automates the monitoring of incubation conditions by periodically measuring environmental variables like temperature and humidity.

The system implements a hybrid architecture where physical and virtual worlds coexist:

- Physical NEST Device: Based on an ESP32 microcontroller, it integrates sensors for temperature, humidity, and weight, alongside actuators such as an intelligent RFID lock and servomotors for automatic doors.

- Simulation Environment: A Python-based software layer that replicates the behavior of multiple nodes, allowing for system scalability testing.

- ThingsBoard Integration: Acts as the primary service orchestrator for data aggregation, rule-based alerts, and digital twin management.

Beyond simple telemetry, NEST features Autonomous Edge Decision-making. For example, if the system detects a weight increase (an egg) but identifying sensors show the hen has left, it automatically triggers actuators to close the nest door, protecting the production from predators.

Code Documentation
------------------

.. toctree::
   :maxdepth: 2
   
   device
   simulation
   thingsboard
   telegram