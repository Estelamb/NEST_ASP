Automated Deployment Workflow
================================

The NEST ecosystem supports a hybrid environment where physical nodes and simulated entities interact seamlessly. To manage this scalability, the project utilizes a batch-driven automated deployment.

Provisioning File (tokens.txt)
------------------------------
The tokens.txt file serves as a local database for device credentials. Each line maps a unique ThingsBoard Access Token to a Device Name.

.. code-block:: text 
   :caption: tokens.txt

   HUyaoCGGK6Pmu8nH3AWr,NEST_2 
   XAWy4XST70V5WmEHwV7h,NEST_3 
   kPfpX4EumVHdRR2icNjP,NEST_4

These tokens allow the simulation to connect as NEST 2, NEST 3, and NEST 4, which are provisioned under the same NEST Device Profile as the physical hardware.

Execution Script (run_all.bat)
------------------------------
The run_all.bat script automates the parallel execution of multiple virtual nodes. It iterates through the provisioning file and launches a separate process for each device.

.. code-block:: batch 
   :caption: run_all.bat

   @echo off 
   for /F "tokens=1,2 delims=," %%A in (tokens.txt) do ( 
      start "%%B" cmd /k python nest_sim.py %%A %%B 
   )

Technical Workflow
------------------

Parsing: The script uses a for loop with a comma delimiter to extract the token (%%A) and the name (%%B).


Parallelism: The start command opens a new command prompt window for each instance, allowing the nodes to run concurrently.


Persistence: The /k flag keeps the terminal open after the script execution, enabling the developer to monitor the local feedback and MQTT logs for each node.


Integration: Once launched, all nodes synchronize their Shared Attributes with ThingsBoard, appearing immediately on the Geographic Map and the Entities Summary Table.