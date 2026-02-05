NEST API Client
===============

This module provides a robust interface for communicating with the IoT Platform backend. It handles all HTTP infrastructure, including authentication persistence, telemetry polling, and bidirectional attribute synchronization.

Operational Logic
-----------------

The client acts as a high-level wrapper around the ``requests`` library, implementing specific patterns for IoT device management:

* **Session Management**: Uses a centralized ``requests.Session`` to maintain persistent headers (JWT Token) and optimize connection pooling across multiple API calls.
* **Two-Phase Attribute Updates**: Implements a "command-and-verify" pattern. When an attribute (like door status or temperature thresholds) is changed, the client performs up to three verification retries to ensure the physical device or the twin has successfully registered the new state.
* **Corpus-Specific Logic**: 
    * **Telemetry**: Fetches time-series data using specific keys (humidity, temperature, weight).
    * **Attributes**: Manages both *Client Attributes* (thresholds, GPS) and *Shared Attributes* (door, RGB status).

Verification Protocol
---------------------

To ensure system reliability, the ``_verify_attribute_change`` method is invoked after any write operation. It handles:

1.  **Numeric Tolerance**: Compares floating-point values (like Temperature) with a small epsilon (0.001) to account for precision differences.
2.  **Retry Backoff**: Introduces a short delay between attempts to allow the backend and the device to synchronize.
3.  **Result Integrity**: Returns a boolean status and a descriptive message, allowing the Telegram interface to report precise errors to the user.

Code Documentation
------------------

.. automodule:: api_client
   :members:
   :undoc-members:
   :show-inheritance: