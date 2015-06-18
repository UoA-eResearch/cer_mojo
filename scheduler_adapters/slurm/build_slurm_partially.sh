#!/bin/bash

killtree() {
    local _pid=${1}
    local _sig=${2}
    kill -stop ${_pid} # needed to stop quickly forking parent from producing children between child killing and parent killing
    for _child in $(ps -o pid --no-headers --ppid ${_pid}); do
        killtree ${_child} ${_sig}
    done
    kill -${_sig} ${_pid}
}

slurmdir='/home/mfel395/SLURM/coding/slurm'

cd $slurmdir
echo "SLURM dir: $slurmdir"
echo "Running configure..."
./configure --sysconfdir=/etc/slurm --libdir=/usr/lib64 1>mybuild.log 2> mybuild.log
echo "Running make..."
make 1>>mybuild.log 2>>mybuild.log &
make_pid=$!

libbuilt="0"
while [ ${libbuilt} -lt "1" ]; do
  sleep 2
  libbuilt=$(find . -name libslurm.o | wc -l)
done

echo "Found libslurm.o. killing build processes..."
killtree ${make_pid} 9

exit 0
