SHELL=/bin/ksh
CC=/usr/bin/g++
CFLAGS=$(MODEFLAGS) -g -I. -I/opt/ibmll/LoadL/scheduler/full/include
LIBS=$(MODEFLAGS) -L/usr/lib64 -L/usr/lib -lllapi -lpthread

all:	get_machine_data get_summary get_jobs get_job_details get_machine_list

clean:
	rm -f get_summary
	rm -f get_machine_data 
	rm -f get_jobs
	rm -f get_job_details
	rm -f get_machine_list

get_machine_data:
	$(CC) $(CFLAGS) $(LIBS) -o $@ $@.cpp

get_summary:
	$(CC) $(CFLAGS) $(LIBS) -o $@ $@.cpp

get_jobs:
	$(CC) $(CFLAGS) $(LIBS) -o $@ $@.cpp

get_job_details:
	$(CC) $(CFLAGS) $(LIBS) -o $@ $@.cpp


get_machine_list:
	$(CC) $(CFLAGS) $(LIBS) -o $@ $@.cpp


