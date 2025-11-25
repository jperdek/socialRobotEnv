#!/bin/bash

# turn on bash's job control
set -m

# Start the primary process and put it in the background
python2.7 ./server.py &

# Start the helper process
/bin/sh -c /choregraphe-2.8.8-ubuntu2204/choregraphe

# the my_helper_process might need to know how to wait on the
# primary process to start before it does its work and returns


# now we bring the primary process back into the foreground
# and leave it there
fg %1