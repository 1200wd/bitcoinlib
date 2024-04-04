Dockerfiles
===========

You can find some basic Dockerfiles here for various system images.

These are used for testing and are not optimized for size and configuration. If you run the container it will
run all unittests.

.. code-block:: bash

    $ cd <move to directory with the Dockerfile you want to use>
    $ docker build -t bitcoinlib .
    $ docker run -it bitcoinlib
