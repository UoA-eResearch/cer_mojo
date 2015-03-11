CC=gcc
SLURM_BASE=/home/mfel395/SLURM/coding/slurm-14.03.3-2
CFLAGS=-I$(SLURM_BASE)/ -I$(SLURM_BASE)/slurm/ -I$(SLURM_BASE)/src/common/ -DHAVE_STDBOOL_H=1 -O2 -pthread 
OUTFILE=get_jobs
# linking against libslurm.so is still required to avoid "undefined references" errors
LFLAGS=-lpthread -lslurm
# libslurm.o has to be built in the slurm source dir prior to running this Makefile
LIBSLURM_OBJECT=../../../slurm-14.03.3-2/src/api/libslurm.o

#OBJECTS = info_job.o info_node.o get_jobs.o
OBJECTS = get_jobs.o

%.o : %.c
	$(CC) -c $(CFLAGS) $< -o $@

all: $(OUTFILE)

$(OUTFILE): $(OBJECTS)
	$(CC) -o $@ $^ $(CFLAGS) $(LIBSLURM_OBJECT) $(LFLAGS)

clean:
	rm -f *~ *.so *.o $(OUTFILE)

