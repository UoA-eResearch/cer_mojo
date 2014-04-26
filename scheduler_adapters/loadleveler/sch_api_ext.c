/*
 * ------------------------------------------------------------------------
 * This is a sample program for the LoadLeveler extended start job API, 
 * intended to be used by an external scheduler
 * ------------------------------------------------------------------------
 */
static char sch_api_ext_sccsid[] = "@(#) src/ll/samples/llsch/sch_api_ext.c, ll.api, ll_rsur2, rsur21042a 1.13.1.4 4/28/10 16:51:57";

/* This sample program shows how the ll_query function of the Query API
 * can be used to obtain information relating to machines and jobs in a 
 * LoadLeveler cluster. It also shows how the functions ll_start_job_ext() 
 * and ll_terminate_job() of the WorkLoad Management API can be used to 
 * start and cancel jobs.
 * Notes:
 *   1. To use the ll_start_job_ext() function, the SCHEDULER_TYPE keyword
 *      of the global LoadLeveler configuration file must be set to API
 *      (SCHEDULER_TYPE = API).  In addition, if switch adapters are to
 *      be assigned, the LoadLeveler configuration file must specify 
 *      AGGREGATE_ADAPTERS=false to make the physical switch adapters
 *      visible to the external scheduler.  Otherwise,  there will appear
 *      to be one adapter for the network that is named networkN where
 *      N is the network ID number.  networkN adapters cannot be used in
 *      the adapter usage list that is passed to ll_start_job_ext.
 *   2. This example will start the first job that is returned.  If more
 *      than one job is returned, it will also cancel the second job.
 *   3. This example requires the job it starts to run on one machine with
 *      two tasks.  Otherwise an error is returned and the job is not started.
 *      This example uses a switch adapter which must have at least two 
 *      windows.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <llapi.h>

/**********************************************************************/
/*                                                                    */
/* Convenience Macros                                                 */
/*                                                                    */
/* These macros call ll_get_data, check the return code and print a   */
/* message if necessary.  They are included to make the code that     */
/* actually accesses the data a little neater                         */
/*                                                                    */
/* GET_DATA calls ll_get_data with the supplied object,               */
/* specification, target variable and format string.  If the call is  */
/* successful, the target variable is set to the value of the         */
/* characteristic being queried and printed.  If the call is not      */
/* successful, a message is printed to stderr                         */
#define GET_DATA(obj,spec,result,fmt) { \
  int rc = ll_get_data(obj,spec,&result); \
  switch(rc) { \
    case -1: fprintf(stderr,"'" #obj "' is not valid as the object parameter to ll_get_data()\n"); break; \
    case -2: fprintf(stderr,"'" #spec "' is not a valid specification parameter to ll_get_data()\n"); break; \
    case 0:  printf(fmt,result); break; \
    default: fprintf(stderr,"Unknown error %d returned from ll_get_data() for '" #spec "'\n",rc); break; \
  } \
}

/* GET_TIME_DATA is used to retrieve, format and print a timestamp    */
/* characteristic.                                                    */
/* It does the same error checking/reporting as GET_DATA              */
#define GET_TIME_DATA(obj,spec,result,fmt) { \
        int rc = ll_get_data(obj,spec,&result); \
        switch(rc) { \
          case -1: fprintf(stderr,"'" #obj "' is not valid as the object parameter to ll_get_data()\n"); break; \
          case -2: fprintf(stderr,"'" #spec "' is not a valid specification parameter to ll_get_data()\n"); break; \
          case 0: { \
            struct tm *curtime; \
            if ( (time_t) result == (time_t) 0) { \
              printf(fmt , ""); \
            } else { \
              curtime = localtime(&result); \
              printf(fmt , asctime(curtime)); \
            } \
          } \
          break; \
          default: fprintf(stderr,"Unknown error %d returned from ll_get_data() for '" #spec "'\n",rc); break; \
          } \
}

/* GET_DATA_LIST is used to retrieve and print a machine              */
/* characteristic that is returned as a list of character strings.    */
/* It does the same error checking/reporting as GET_DATA              */
/* label is the line printed before the list starts and sep is the    */
/* separation between elements.  Typically it would either be a comma */
/* or a newline                                                       */
#define GET_DATA_LIST(obj,spec,list,item,label,sep)  { \
    int rc = ll_get_data(obj,spec,&list); \
    switch(rc) { \
    case -1: fprintf(stderr,"'" #obj "' is not valid as the object parameter to ll_get_data()\n"); break; \
    case -2: fprintf(stderr,"'" #spec "' is not a valid specification parameter to ll_get_data()\n"); break; \
    case 0:  \
      if((list!=NULL)&&(list[0]!=NULL)) \
	{ \
	  printf(label ":\n"); \
	  for(item = list;*item!=NULL;item++) \
	    { \
	      printf("\t%s" sep,*item); \
	      free(*item); \
	    } \
	} else { printf("No " label "\n"); } \
      break; \
    default: fprintf(stderr,"Unknown error %d returned from ll_get_data() for '" #spec "'\n",rc); break;  \
    } \
  }

/*                                                                    */
/* End of Convenience Macros                                          */
/*                                                                    */
/**********************************************************************/


void show_LL_machine(LL_element *machine);
void show_LL_job(LL_element *);
void error_report(int);
void show_set_rc(int rc);
void start_job(LL_element * job);
void cancel_job(LL_element * job);
void show_getobjs_rc(int rc);


/* These variables will capture info needed to start a job            */
char * use_machine = NULL;
uint64_t use_network = 0llu;

main(int argc, char **argv) {
	int  n, i, rc;
	int machine_count;
	int job_count;
	LL_element * query_elem;
	LL_element * machine;
	LL_element * job;

	int start=1;

	if((argc>1)&&(0==strcmp("-d",argv[1])))
		start = 0;

	/* First we need to obtain a query element which is used to pass     */
	/* parameters in to the machine query                                */
	if ((query_elem = ll_query(MACHINES)) == NULL) {
		fprintf(stderr,"Unable to obtain query element\n");
		/* without the query object we will not be able to do anything */
		exit(-1);
	}

	/* Get information relating to machines in the LoadLeveler cluster. */

	printf("Machines Information =====================================\n\n");
	/* QUERY_ALL: we are querying all machines                           */
	/* NULL: since we are querying all machines we do not need to        */
	/*       specify a filter to indicate which machines                 */
	/* ALL_DATA: we want all the information available about the machine */
	rc=ll_set_request(query_elem,QUERY_ALL,NULL,ALL_DATA);
	if(rc<0) {
		show_set_rc(rc);
	} else {

		/* If successful, ll_get_objs() returns the first object that    */
		/* satisfies the criteria that are set in the query element and  */
		/* the parameters.  In this case those criteria are:             */
		/* A machine (from the type of query object)                     */
		/* LL_CM: that the negotiator knows about                        */
		/* NULL: since there is only one negotiator we don't have to     */
		/*       specify which host it is on                             */
		/* The number of machines is returned in machine_count and the   */
		/* return code is returned in rc                                 */
		machine = ll_get_objs(query_elem,LL_CM,NULL,&machine_count,&rc);
		if(rc<0) {
			show_getobjs_rc(rc);
		} else {
			printf("Number of Machines = %d\n", machine_count);
			i = 0;
			while(machine!=NULL) {
				printf("------------------------------------------------------\n");
				printf("Machine %d:\n", i);
				show_LL_machine(machine);
				printf("\n");
				i++;
				machine = ll_next_obj(query_elem);
			}
			if(ll_free_objs(query_elem) == -1) {
				fprintf(stderr,"Attempt to free invalid query element\n");
			}
		}
		if(ll_deallocate(query_elem) == -1) {
			fprintf(stderr,"Attempt to deallocate invalid query element\n");
		}
	}

	/* First we need to obtain a query element which is used to pass     */
	/* parameters in to the jobs query                                   */
	if ((query_elem = ll_query(JOBS)) == NULL) {
		fprintf(stderr,"Unable to obtain query element\n");
		/* without the query object we will not be able to do anything */
		exit(-1);
	}

	/* Get information relating to Jobs in the LoadLeveler cluster. */
	printf("Jobs Information ========================================\n\n");
	/* QUERY_ALL: we are querying all jobs                               */
	/* NULL: since we are querying all jobs we do not need to            */
	/*       specify a filter to indicate which jobs                     */
	/* ALL_DATA: we want all the information available about the job     */
	rc=ll_set_request(query_elem,QUERY_ALL,NULL,ALL_DATA);
	if(rc<0) {
		show_set_rc(rc);
	} else {
		/* If successful, ll_get_objs() returns the first object that    */
		/* satisfies the criteria that are set in the query element and  */
		/* the parameters.  In this case those criteria are:             */
		/* A job (from the type of query object)                         */
		/* LL_CM: that the negotiator knows about                        */
		/* NULL: since there is only one negotiator we don't have to     */
		/*       specify which host it is on                             */
		/* The number of jobs is returned in job_count and the           */
		/* return code is returned in rc                                 */
		job = ll_get_objs(query_elem,LL_CM,NULL,&job_count,&rc);
		if(rc<0) {
			show_getobjs_rc(rc);
		} else {
			printf("Number of Jobs = %d\n", job_count);
			i = 0;
			while(job!=NULL) {
				printf("------------------------------------------------------\n");
				printf("Job Number %d:\n", i);
				show_LL_job(job);
				if(start==1) {
					if(i==0) {
						start_job(job);
					}
					if(i==1) {
						cancel_job(job);
					}
				}
				printf("\n");
				i++;
				job = ll_next_obj(query_elem);
			}
			if(ll_free_objs(query_elem) == -1) {
				fprintf(stderr,"Attempt to free invalid query element\n");
			}
		}
		if(ll_deallocate(query_elem) == -1) {
			fprintf(stderr,"Attempt to deallocate invalid query element\n");
		}
	}


}

void
start_job(LL_element * job) {
	int iBuffer;
	char * pcBuffer;
	char * pChar;
	LL_element * step;
	int rc;

	/* Invoke the function ll_start_job_ext() to start a job step.    */
	/* This operation is meaningful only when used with an            */
	/* external scheduler (SCHEDULER_TYPE = API).                     */

	LL_start_job_info_ext *start_info;

	if(use_machine == NULL) {
		fprintf(stderr,"No machine available to start job on\n");
		return;
	}

	start_info = (LL_start_job_info_ext *)(malloc(sizeof(LL_start_job_info_ext)));
	if(start_info == NULL) {
		fprintf(stderr, "Out of memory.\n");
		return;
	}

	/* Create a NULL terminated list of target machines.  Each task      */
	/* must have an entry in this list and the entries for tasks on the  */
	/* same machine must be sequential.  For example, if a job is to run */
	/* on two machines, A and B, and three tasks are to run on each      */
	/* machine, the list would be: AAABBB                                */
	/* Any specifications on the job when it was submitted such as       */
	/* nodes, total_tasks or tasks_per_node must be explicitly queried   */
	/* and honored by the external scheduler in order to take effect.    */
	/* They are not automatically enforced by LoadLeveler when an        */
	/* external scheduler is used.                                       */
	/*                                                                   */
	/* In this example, the job will only be run on one machine          */
	/* with two tasks so the machine list consists of only 2 entries     */
	/* pointing to the same machine (plus the terminating NULL entry)    */

	start_info->nodeList = (char **)malloc(3*sizeof(char *));
	if (!start_info->nodeList) {
		fprintf(stderr, "Out of memory.\n");
		return;
	}
	start_info->nodeList[0] = strdup(use_machine);
	start_info->nodeList[1] = strdup(use_machine);
	start_info->nodeList[2] = NULL;

	/* Retrieve information from the job to populate the start_info      */
	/* structure                                                         */
	/* In the interest of brevity, the success of the ll_get_data()      */
	/* is not tested.  In a real application it should be                 */

	/* The version number is set from the header that is included when   */
	/* the application using the API is compiled.  This allows for       */
	/* checking that the application was compiled with a version of the  */
	/* API that is compatible with the version in the library when the   */
	/* application is run.                                               */
	start_info->version_num = LL_PROC_VERSION;

	/* Get the first step of the job to start                            */
	ll_get_data(job,LL_JobGetFirstStep,&step);
	if(step==NULL) {
		printf("No step to start\n");
		return;
	}

	/* In order to set the submitting host, cluster number and proc      */
	/* number in the start_info structure, we need to parse it out of    */
	/* the step id                                                       */

	/* First get the submitting host and save it                         */
	ll_get_data(job,LL_JobSubmitHost,&pcBuffer);
	start_info->StepId.from_host = strdup(pcBuffer);
	free(pcBuffer);

	rc = ll_get_data(step, LL_StepID, &pcBuffer);

	/* We need to skip over the submitting host to get to the job and    */
	/* step numbers                                                      */
	pChar = pcBuffer+strlen(start_info->StepId.from_host);
	/* The next segment is the cluster or job number                     */
	pChar = strtok(pChar,".");
	start_info->StepId.cluster=atoi(pChar);
	/* The last token is the proc or step number                         */
	pChar = strtok(NULL,".");
	start_info->StepId.proc = atoi(pChar);
	free(pcBuffer);

	printf("Start Job Step %s.%d.%d ========================================\n\n",
	       start_info->StepId.from_host,
	       start_info->StepId.cluster,
	       start_info->StepId.proc);

	/* For each protocol (eg. MPI or LAPI) on each task, we need to      */
	/* specify which adapter to use, whether a window is being used      */
	/* (subsystem = "US") or not (subsytem="IP").  If windows are used,  */
	/* the number of windows must be specified.                          */
	/*                                                                   */
	/* This example starts the job with two tasks on one machine, using  */
	/* one switch adapter window on each task.  The protocol is forced   */
	/* to MPI.  An actual external scheduler application would check the */
	/* steps requirements and its  adapter requirements of the step with */
	/* ll_get_data                                                       */

	start_info->adapterUsageCount = 0;
	start_info->adapterUsage = NULL;

	start_info->networkUsageCount = 0;
	start_info->networkUsage = NULL;

#ifdef ETHERNET
	start_info->networkUsageCount = 1;
	start_info->networkUsage = (LL_NETWORK_USAGE *)malloc(start_info->networkUsageCount * sizeof(LL_NETWORK_USAGE));

	start_info->networkUsage[0].protocol = strdup("MPI");
	start_info->networkUsage[0].subsystem = strdup("IP");

	start_info->networkUsage[0].network_type = strdup("ethernet");

	start_info->networkUsage[0].windows_per_instance = 0;
	start_info->networkUsage[0].instances_per_task = 1;
#endif

#ifdef SN_SINGLE
	use_network = 18338657682652659713llu;		// change to any valid network.

	start_info->networkUsageCount = 1;
	start_info->networkUsage = (LL_NETWORK_USAGE *)malloc(start_info->networkUsageCount * sizeof(LL_NETWORK_USAGE));

	start_info->networkUsage[0].protocol = strdup("MPI");
	start_info->networkUsage[0].subsystem = strdup("US");

	start_info->networkUsage[0].network_id = use_network;
	start_info->networkUsage[0].network_type = strdup("switch");

	start_info->networkUsage[0].windows_per_instance = 1;
	start_info->networkUsage[0].instances_per_task = 1;
#endif

#ifdef SN_ALL
	start_info->networkUsageCount = 1;
	start_info->networkUsage = (LL_NETWORK_USAGE *)malloc(start_info->networkUsageCount * sizeof(LL_NETWORK_USAGE));

	start_info->networkUsage[0].protocol = strdup("MPI");
	start_info->networkUsage[0].subsystem = strdup("US");

	start_info->networkUsage[0].network_id = 0;		// sn_all
	start_info->networkUsage[0].network_type = strdup("switch");

	start_info->networkUsage[0].windows_per_instance = 1;
	start_info->networkUsage[0].instances_per_task = 1;
#endif

	if ((rc = ll_start_job_ext(start_info)) != API_OK) {
		error_report(rc);
	} else {
		printf("ll_start_job_ext() invoked to start job step: %s.%d.%d on machine: %s.\n\n",
		       start_info->StepId.from_host, start_info->StepId.cluster,
		       start_info->StepId.proc,  start_info->nodeList[0]);
	}
	free(start_info->nodeList[1]);
	free(start_info->nodeList[0]);
	free(start_info->nodeList);
	free(start_info->StepId.from_host);
	if (start_info->networkUsage != NULL) {
		free(start_info->networkUsage[0].protocol);
		free(start_info->networkUsage[0].subsystem);
		free(start_info->networkUsage[0].network_type);
		free(start_info->networkUsage);
	}
	free(start_info);

	/* reset other variables to initial values */
	if (use_machine != NULL) {
		free(use_machine);
		use_machine=NULL;
	}
}

void
cancel_job(LL_element * job) {
	LL_terminate_job_info *cancel_info;
	LL_element * step;
	char * pChar;
	int rc;
	char * pcBuffer;

	/* First, request a structure that will be populated with           */
	/* information about the job to be canceled                         */
	cancel_info = (LL_terminate_job_info *)malloc(sizeof(LL_terminate_job_info));
	if (!cancel_info) {
		fprintf(stderr, "Out of memory.\n");
		exit(1);
	}

	/* Retrieve information from the job to populate the start_info      */
	/* structure                                                         */
	/* In the interest of brevity, the success of the ll_get_data()      */
	/* is not tested.  In a real application it should be                 */

	/* The version number is set from the header that is included when   */
	/* the application using the API is compiled.  This allows for       */
	/* checking that the application was compiled with a version of the  */
	/* API that is compatible with the version in the library when the   */
	/* application is run.                                               */
	cancel_info->version_num = LL_PROC_VERSION;

	/* Get the first step of the job to cancel                           */
	ll_get_data(job,LL_JobGetFirstStep,&step);
	if(step==NULL) {
		printf("No step to cancel\n");
		return;
	}

	/* In order to set the submitting host, cluster number and proc      */
	/* number in the start_info structure, we need to parse it out of    */
	/* the step id                                                       */

	/* First get the submitting host and save it                         */
	ll_get_data(job,LL_JobSubmitHost,&pcBuffer);
	cancel_info->StepId.from_host = strdup(pcBuffer);
	free(pcBuffer);

	rc = ll_get_data(step, LL_StepID, &pcBuffer);

	/* We need to skip over the submitting host to get to the job and    */
	/* step numbers                                                      */
	pChar = pcBuffer+strlen(cancel_info->StepId.from_host);
	/* The next segment is the cluster number                            */
	pChar = strtok(pChar,".");
	cancel_info->StepId.cluster=atoi(pChar);
	/* The last token is the proc or step number                         */
	pChar = strtok(NULL,".");
	cancel_info->StepId.proc = atoi(pChar);
	free(pcBuffer);

	printf("Cancel Job Step %s.%d.%d ========================================\n\n",
	       cancel_info->StepId.from_host,
	       cancel_info->StepId.cluster,
	       cancel_info->StepId.proc);

	cancel_info->msg = NULL;

	if ((rc = ll_terminate_job(cancel_info)) != API_OK) {
		error_report(rc);
	} else {
		printf("ll_terminate_job() invoked to cancel job step: %s.%d.%d.\n\n",
		       cancel_info->StepId.from_host, cancel_info->StepId.cluster,
		       cancel_info->StepId.proc);
	}

	free(cancel_info->StepId.from_host);
	free(cancel_info);
}

void
show_LL_machine(LL_element *machine) {
	int i;
	char * machine_name;
	char * pcBuffer;
	char ** ppcBuffer;
	char ** ppChar;
	time_t tBuffer;
	int iBuffer;
	int * piBuffer;
	int64_t i64Buffer;
	double dBuffer;
	LL_element * adapter;

	GET_DATA(machine,LL_MachineName,machine_name,"Node name = %s\n");

	GET_TIME_DATA(machine,LL_MachineTimeStamp,tBuffer,"Timestamp = %s\n");
	GET_DATA(machine,LL_MachineVirtualMemory,iBuffer,"Virtual Memory = %d KB\n");
	GET_DATA(machine,LL_MachineVirtualMemory64,i64Buffer,"Virtual Memory (64-bit) = %lld KB\n");
	GET_DATA(machine,LL_MachineRealMemory,iBuffer,"Real Memory = %d MB\n");
	GET_DATA(machine,LL_MachineRealMemory64,i64Buffer,"Real Memory (64-bit) = %lld MB\n");
	GET_DATA(machine,LL_MachineDisk,iBuffer,"Disk = %d KB\n");
	GET_DATA(machine,LL_MachineDisk64,i64Buffer,"Disk (64-bit) = %lld KB\n");
	GET_DATA(machine,LL_MachineLoadAverage,dBuffer,"LoadAvg = %f\n");
	GET_DATA(machine,LL_MachineSpeed,dBuffer,"Speed = %f\n");

	/* Getting the pool list is a two step process: first get get the    */
	/* size of the list and then the list itself.  To print it, we walk  */
	/* the list up to the returned size.  There are NO built-in checks   */
	/* that would prevent us from walking off the end of the list!       */
	{
		int rc = ll_get_data(machine,LL_MachinePoolListSize,&iBuffer);
		switch(rc) {
		case -1:
			fprintf(stderr,"'machine' is not valid as the object parameter to ll_get_data()\n");
			break;
		case -2:
			fprintf(stderr,"'LL_MachinePoolListSize' is not a valid specification parameter to ll_get_data()\n");
			break;
		case 0: {
				int rc = ll_get_data(machine,LL_MachinePoolList,&piBuffer);
				switch(rc) {
				case -1:
					fprintf(stderr,"'machine' is not valid as the object parameter to ll_get_data()\n");
					break;
				case -2:
					fprintf(stderr,"'LL_MachinePoolList' is not a valid specification parameter to ll_get_data()\n");
					break;
				case 0:

					printf("Pool list = ");
					{
						int i;
						for(i=0;i<iBuffer-2;i++) {
							printf("%d, ",piBuffer[i]);
						}
						if(iBuffer>0)
							printf("%d",piBuffer[i]);
						/* Allocated list needs t be freed                         */
						free(piBuffer);
					}
					printf("\n");
					break;

				default:
					fprintf(stderr,"Unknown error %d returned from ll_get_data() for 'LL_MachinePoolList'\n",rc);
					break;
				}
			}
			break;
		default:
			fprintf(stderr,"Unknown error %d returned from ll_get_data() for 'LL_MachinePoolListSize'\n",rc);
			break;
		}
	}

	GET_DATA(machine,LL_MachineCPUs,iBuffer,"Cpus = %d\n");
	GET_DATA(machine,LL_MachineKbddIdle,iBuffer,"Seconds since last interactive activity = %d\n");
	GET_DATA(machine,LL_MachineArchitecture,pcBuffer,"Architecture = %s\n");
	free(pcBuffer);
	GET_DATA(machine,LL_MachineOperatingSystem,pcBuffer,"Operating System = %s\n");
	free(pcBuffer);
	/* Machine mode is Batch, Interactive or General                     */
	GET_DATA(machine,LL_MachineMachineMode,pcBuffer,"Machine mode = %s\n");
	free(pcBuffer);
	GET_DATA(machine,LL_MachineStartdState,pcBuffer,"Startd State = %s\n");
	free(pcBuffer);
	GET_DATA(machine,LL_MachineScheddTotalJobs,iBuffer,"Number of jobs submitted to schedd = %d\n");
	GET_DATA(machine,LL_MachineScheddRunningJobs,iBuffer,"Number of running jobs managed by this schedd = %d\n");

	GET_DATA_LIST(machine,LL_MachineStepList,ppcBuffer,ppChar,"Job Steps on this machine","\n");
	free(ppcBuffer);
	GET_DATA_LIST(machine,LL_MachineAdapterList,ppcBuffer,ppChar,"Adapters on this machine","\n");
	free(ppcBuffer);
	GET_DATA_LIST(machine,LL_MachineFeatureList,ppcBuffer,ppChar,"Features on this machine","\n");
	free(ppcBuffer);
	{
		int rc;
		typedef struct _class_struct {
			char * name;
			int count;
		}
		ClassInfo_t;
		ClassInfo_t * class_info;
		int class_count=0;
		int total_count=0;

		rc = ll_get_data(machine,LL_MachineAvailableClassList,&ppcBuffer);
		switch(rc) {
		case -1: fprintf(stderr,"'machine' is not valid as the object parameter to ll_get_data()\n"); break;
		case -2: fprintf(stderr,"'LL_MachineAvailableClassList' is not a valid specification parameter to ll_get_data()\n"); break;
		case 0:
			if((ppcBuffer!=NULL)&&(ppcBuffer[0]!=NULL)) {
				int i;
				printf("Class list:\n");
				for(ppChar = ppcBuffer;*ppChar != NULL;ppChar++) {
					total_count++;
				}
				/* We allocate as if each class name is unique to guarantee enough entries */
				class_info = (ClassInfo_t *)malloc(total_count*sizeof(ClassInfo_t));
				for(ppChar = ppcBuffer;*ppChar != NULL;ppChar++) {
					for(i=0;i<class_count;i++)
						if(strcmp(*ppChar,class_info[i].name)==0) {
							break;
						}
					if(i<class_count) {
						/* Found existing entry for same class */
						class_info[i].count++;
					} else {
						/* Have not seen this class before */
						class_info[i].name = strdup(*ppChar);
						class_info[i].count = 1;
						class_count++;
					}
					free(*ppChar);
				}
				free(ppcBuffer);
				for(i=0;i<class_count;i++) {
					printf("\t%s: %d\n",class_info[i].name,class_info[i].count);
					free(class_info[i].name);
					class_info[i].name = NULL;
				}
				free(class_info);
			} else { printf("No Class list\n"); }
			break;
		default: fprintf(stderr,"Unknown error %d returned from ll_get_data() for 'LL_MachineAvailableClassList'\n",rc); break;
		}
	}

	printf("Adapters\n");
	ll_get_data(machine,LL_MachineGetFirstAdapter,&adapter);
	while(adapter != NULL) {
		GET_DATA(adapter,LL_AdapterName,pcBuffer,"\tName = %s\n");
		GET_DATA(adapter,LL_AdapterMemory64,i64Buffer,"\tMemory = %lld\n");
		GET_DATA(adapter,LL_AdapterTotalWindowCount,iBuffer,"\tTotal windows = %d\n");
		free(pcBuffer);
		printf("\n");
		ll_get_data(machine,LL_MachineGetNextAdapter,&adapter);
	}

	/* If we haven't found a machine on which to start a job yet */
	/* then use this machine                                     */
	/* information for later                                     */
	if(use_machine==NULL) {
		use_machine = strdup(machine_name);
		printf("Start job on %s\n", use_machine);
	}
	free(machine_name);
}

void
show_LL_job(LL_element *job) {
	int i;
	int max_mach_count;
	int min_mach_count;
	LL_element * step;
	LL_element * node;
	time_t tBuffer;
	char * pcBuffer;
	int iBuffer;
	int64_t i64Buffer;

	GET_DATA(job,LL_JobName,pcBuffer,"Job name = %s\n");
	free(pcBuffer);
	GET_TIME_DATA(job,LL_JobSubmitTime,tBuffer,"Job submit time = %s\n");
	GET_DATA(job,LL_JobStepCount,iBuffer,"Number of job steps = %d\n");

	step=NULL;
	{
		int rc = ll_get_data(job,LL_JobGetFirstStep,&step);
		switch(rc) {
		case -1:
			fprintf(stderr,"'job' is not valid as the object parameter to ll_get_data()\n");
			break;
		case -2:
			fprintf(stderr,"'LL_JobGetFirstStep' is not a valid specification parameter to ll_get_data()\n");
			break;
		case 0:
			break;
		default:
			fprintf(stderr,"Unknown error %d returned from ll_get_data() for 'LL_JobStepCount'\n",rc);
			break;
		}
	}

	while(step!=NULL) {

		GET_DATA(step,LL_StepID,pcBuffer,"Step ID = %s\n");
		free(pcBuffer);
		GET_TIME_DATA(step,LL_StepDispatchTime,tBuffer,"Dispatch Time = %s\n");
		GET_DATA(step,LL_StepState,iBuffer,"State = %d\n");
		GET_DATA(step,LL_StepName,pcBuffer,"Name = %s\n");
		free(pcBuffer);
		GET_DATA(step,LL_StepJobClass,pcBuffer,"Class = %s\n");
		free(pcBuffer);
		printf("Hard Limits:\n");
		GET_DATA(step,LL_StepCpuLimitHard,iBuffer,"\tCPU           = %d\n");
		GET_DATA(step,LL_StepWallClockLimitHard,iBuffer,"\tWallClock     = %d\n");
		GET_DATA(step,LL_StepFileLimitHard,iBuffer,"\tFile          = %d\n");
		GET_DATA(step,LL_StepFileLimitHard64,i64Buffer,"\tFile (64-bit) = %lld\n");
		printf("Soft Limits:\n");
		GET_DATA(step,LL_StepCpuLimitSoft,iBuffer,"\tCPU           = %d\n");
		GET_DATA(step,LL_StepWallClockLimitSoft,iBuffer,"\tWallClock     = %d\n");
		GET_DATA(step,LL_StepFileLimitSoft,iBuffer,"\tFile          = %d\n");
		GET_DATA(step,LL_StepFileLimitSoft64,i64Buffer,"\tFile (64-bit) = %lld\n");

		max_mach_count=0;
		min_mach_count=0;
		ll_get_data(step,LL_StepGetFirstNode,&node);
		while(node!=NULL) {
			ll_get_data(node,LL_NodeMaxInstances,&iBuffer);
			max_mach_count += iBuffer;
			ll_get_data(node,LL_NodeMinInstances,&iBuffer);
			min_mach_count += iBuffer;
			ll_get_data(step,LL_StepGetNextNode,&node);
		}
		if(max_mach_count==min_mach_count)
			printf("Step runs on %d machine(s)\n",max_mach_count);
		else
			printf("Step runs on between %d and %d machines\n",min_mach_count,max_mach_count);
		ll_get_data(job,LL_JobGetNextStep,&step);
	}
}


void error_report(int rtc) {
	switch (rtc) {
	case API_INVALID_INPUT:
		fprintf(stderr, "Invalid parameter.\n");
		break;

	case API_CANT_MALLOC:
		fprintf(stderr, "Out of memory.\n");
		break;

	case API_CANT_CONNECT:
		fprintf(stderr, "Can't connect to CM.\n");
		break;

	case API_CONFIG_ERR:
		fprintf(stderr, "Configuration error.\n");
		break;

	case API_CANT_TRANSMIT:
		fprintf(stderr, "Transaction problem.\n");
		break;

	case API_CANT_AUTH:
		fprintf(stderr, "Not an administrator.\n");
		break;

	case API_CANT_FIND_PROC:
		fprintf(stderr, "No such step in CM.\n");
		break;

	case API_WRNG_PROC_VERSION:
		fprintf(stderr, "Wrong proc version number.\n");
		break;

	case API_WRNG_PROC_STATE:
		fprintf(stderr, "Wrong step state to start.\n");
		break;

	case API_MACH_NOT_AVAIL:
		fprintf(stderr, "Machine not available.\n");
		break;

	case API_CANT_FIND_RUNCLASS:
		fprintf(stderr, "Run class not available.\n");
		break;

	case API_REQ_NOT_MET:
		fprintf(stderr, "Requirements not met.\n");
		break;

	case API_WRNG_MACH_NO:
		fprintf(stderr, "Wrong machine number.\n");
		break;

	case API_LL_SCH_ON:
		fprintf(stderr, "LL scheduler on.\n");
		break;

	case API_MACH_DUP:
		fprintf(stderr, "Duplicated machine names.\n");
		break;

	case API_NO_DCE_CRED:
		fprintf(stderr, "No dce credentials.\n");
		break;

	case API_INSUFFICIENT_DCE_CRED:
		fprintf(stderr, "DCE credential lifetime less than 300 seconds.\n");
		break;

	case API_64BIT_DCE_ERR:
		fprintf(stderr, "LoadLeveler 64-bit APIs not supported when DCE is enabled.\n");
		break;

	case API_BAD_ADAPTER_USAGE:
		fprintf(stderr, "Bad Adapter Usage. \n");
		break;

	case API_BAD_ADAPTER_DEVICE:
		fprintf(stderr, "Bad Adapter Device. \n");
		break;

	case API_BAD_ADAPTER_USAGE_COUNT:
		fprintf(stderr, "Bad Adapter Usage Count. \n");
		break;

	case API_BAD_ADAPTER_USAGE_PATTERN:
		fprintf(stderr, "Bad Adapter Usage Pattern. \n");
		break;

	case API_BAD_PROTOCOL:
		fprintf(stderr, "Bad Adapter Usage Protocol. \n");
		break;

	case API_INCOMPATIBLE_PROTOCOL:
		fprintf(stderr, "Incompatible Adapter Usage Protocols. \n");
		break;

	case API_BAD_COMMUNICATION_SUBSYSTEM:
		fprintf(stderr, "Bad Adapter Usage Communication Subsystem. \n");
		break;

	default:
		fprintf(stderr, "Unknown error (%d).\n",rtc);
	}
}

void
show_set_rc(int rc) {
	switch(rc) {
	case -1:
		fprintf(stderr,"Invalid query element parameter to ll_set_request()\n");
		break;
	case -2:
		fprintf(stderr,"Invalid query flag parameter to ll_set_request()\n");
		break;
	case -3:
		fprintf(stderr,"Invalid object filter parameter to ll_set_request()\n");
		break;
	case -4:
		fprintf(stderr,"Invalid data filter parameter to ll_set_request()\n");
		break;
	case -5:
		fprintf(stderr,"System error in ll_set_request()\n");
		break;
	default:
		fprintf(stderr,"Unknown error %d returned from ll_set_request()\n",rc);
	}
}

void
show_getobjs_rc(int rc) {
	switch(rc) {
	case -1:
		fprintf(stderr,"Invalid query element parameter to ll_get_objs()\n");
		break;
	case -2:
		fprintf(stderr,"Invalid daemon parameter to ll_get_objs()\n");
		break;
	case -3:
		fprintf(stderr,"Cannot resolve hostname parameter to ll_get_objs()\n");
		break;
	case -4:
		fprintf(stderr,"Request type for specified daemon is not a valid parameter to ll_get_objs()\n");
		break;
	case -5:
		fprintf(stderr,"System error in ll_get_objs()\n");
		break;
	case -6:
		fprintf(stderr,"No valid objects meet the request to ll_get_objs()\n");
		break;
	case -7:
		fprintf(stderr,"Configuration error in call to ll_get_objs()\n");
		break;
	case -9:
		fprintf(stderr,"Connection to daemon failed during call to ll_get_objs()\n");
		break;
	case -10:
		fprintf(stderr,"Error processing history file in call to ll_get_objs()\n");
		break;
	case -11:
		fprintf(stderr,"History file must be specified in the hostname parameter to ll_get_objs()\n");
		break;
	case -12:
		fprintf(stderr,"Unable to access the history file in call to ll_get_objs()\n");
		break;
	case -13:
		fprintf(stderr,"DCE identity of program calling ll_get_objs()  can not be established\n");
		break;
	case -14:
		fprintf(stderr,"No DCE credentials in call to ll_get_objs()\n");
		break;
	case -15:
		fprintf(stderr,"DCE credentials within 300 secs of expiration when ll_get_objs() called\n");
		break;
	case -16:
		fprintf(stderr,"64-bit API is not supported when DCE is enabled for call to ll_get_objs()\n");
		break;
	default:
		fprintf(stderr,"Unknown error %d returned from ll_get_objs()\n",rc);
	}
}
