.. _coding_standards:

Coding standard
###############

- :ref:`**General** <general_section>`
- Python
- ROS (Robot Operating System)

----------

.. _general_section:

General
-------

- Use spaces, not tables
- Avoid adding trailing whitespace as it creates noise in the diffs.

Python
------

- Comments should not exceed 80 columns, code should not exceed 120 columns.
- All code must be compatible with Python 2.7 and 3.7.
- `Pylint <https://www.pylint.org/>`__ should not give any error or warning (few exceptions apply with external classes like :code:`numpy` and :code:`pygame`, see our :code:`.pylintrc`).
- Python code follows `PEP8 style guide <https://peps.python.org/pep-0008/>`__ (use :code:`autopep8` whenever possible).

ROS
---

- Follow the ROS `C++ Style Guide <http://wiki.ros.org/CppStyleGuide>`__ for C++ code.
- Python code for ROS follows the same guidelines as general Python code, including PEP8.
- Always use `roslint <http://wiki.ros.org/roslint>`__ to check code style.
- Ensure compatibility with both ROS Melodic and ROS Noetic.
- Use `catkin_lint <http://fkie.github.io/catkin_lint/>`__ to ensure CMakeLists.txt and package.xml files adhere to best practices.
- Document all ROS nodes with detailed `ROS node API documentation <http://wiki.ros.org/roscpp/Overview/NodeHandle%20API>`__.
- Always provide launch files for starting nodes and ensure they are well-documented.