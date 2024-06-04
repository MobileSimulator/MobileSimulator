.. _documentation:

MR-Sim Documentation
####################

Welcome to the MR-Sim (Mobile Robot Simulator) documentation.

The **MR-Sim** is a framework based on `NVIDIA
Omniverse <https://docs.omniverse.nvidia.com/>`__ and `Isaac
Sim <https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/overview.html>`__. It is built on popular mobile robots that include Four-differential, Ackermann, and Dynamic control systems. The simulator provides models of various robots such as `Husky UGV <https://clearpathrobotics.com/husky-unmanned-ground-vehicle-robot/>`__, `QCar <https://www.quanser.com/products/qcar/>`__, `Franka Research 3 <https://franka.de/research>`__, and a integration of `Husky + FR3 <https://www.youtube.com/watch?v=cwqMOhF1UuI>`__. At this moment, the simulator is under development, and more features will be provided in the future, including slam, real-time ROS connection, and more. In any case, here are a few suggestions for newcomers.


- **Install Isaac Sim**. Either follow the :ref:`Quick start installation <quick_start_installation>` to get a Isaac Sim release for a desired platform.
- **Simple Example of API**. The section titled 

Developer Team
~~~~~~~~~~~~~~

The **Mobile Robot Simulator** is an open-source framework, started by Ji Sue Lee and Dong Beom Kim in April/2024. It is a tool that was create with the original purpose of devloping our intuition. This project is planned to take a total of 1 year, with completion expected by 2025.

- Project Founder
   - `Ji Sue Lee <https://leejisue.github.io/>`__, a Ph.D. candidate at Hanyang University in Seoul, South Korea, working in the Control and Optimization Lab.
- Architecture
   - `Ji Sue Lee <https://leejisue.github.io/>`__
   - `Dong Beom Kim <https://github.com/KDB0814>`__
- Robot Dynamic Simulation and Control
   - `Ji Sue Lee <https://leejisue.github.io/>`__
   - `Dong Beom Kim <https://github.com/KDB0814>`__
- Applications
   - `Ji Sue Lee <https://leejisue.github.io/>`__
   - `Dong Beom Kim <https://github.com/KDB0814>`__

.. toctree::
   :maxdepth: 3
   :caption: Getting Started:

   source/setup/introduction
   source/setup/installation
   source/setup/developer

.. toctree::
   :maxdepth: 3
   :caption: MR-Sim TOPICS:

   source/topics/robots
   source/topics/environments
   source/topics/sensors

.. toctree::
   :maxdepth: 3
   :caption: Guidlines:

   source/references/contributing
   source/references/changelog
   source/references/standard

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
