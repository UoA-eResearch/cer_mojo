static char ll_get_machine_list_sccsid[] = "@(#) src/ll/samples/llmpich/ll_get_machine_list.c, ll.linux, ll_rsur2, rsur21042a 1.9 4/16/10 15:28:01";

/*
 * Program name: ll_get_machine_list.c
 * ---------------------------------------------------------------------
 * This program shows how LoadLeveler's Data Access API can be used
 * to obtain information about machines that have been assigned by LoadLeveler
 * to run various "tasks" of a user job step. It is intended for use mostly
 * with MPICH and MPICH-GM job steps. The name of the job step is from
 * the environment variable LOADL_STEP_ID that is set by LoadLeveler before
 * the job is started.  For each task of the job step, the name of the machine
 * assigned to run the task is written to standard output.
 * Note: Serial and Parallel jobs only. NQS, PVM, Blue Gene jobs not supported.
 *
 * Input:
 *   - LOADL_STEP_ID environment variable
 *
 * Output:
 *   - stdout: List of machines that have been selected by LoadLeveler
 *             to run the tasks of the job step. One machine per line,
 *             sorted by task instance ID.
 *
 *             NOTE: If -s option is used, then write machine list as a single
 *             string. No new line (\n) at the end of the string.
 *
 *   - stderr: Error messages.
 *
 * Return code:
 *    = 0: Success. Machine list created.
 *    = 1: No machine has been assigned to the job step.
 *    = 2: All other errors.
 *
 * Linux: compile and link this program with:
 *    g++ -c ll_get_machine_list.c -I/opt/ibmll/LoadL/scheduler/full/include
 *    g++ -o ll_get_machine_list ll_get_machine_list.o -lllapi
 * g++ must be used instead of gcc since the LoadLeveler libllapi.so library is
 * a C++ library.
 * ---------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include "llapi.h"

void ll_get_data_error(const char *, int);
int ll_task_info_compare(const void *, const void *);
void ll_out_of_memory(void);

typedef struct {
	int   task_instance_id;
	char *task_instance_machine_name;
}
LL_TASK_INFO;

#define LL_TASK_INFO_ARRAY_SIZE_BASE 5000
#define LL_TASK_INFO_ARRAY_SIZE_INCREMENT 5000
int ll_task_info_array_size = LL_TASK_INFO_ARRAY_SIZE_BASE;
LL_TASK_INFO  **ll_task_info_array;

int
main(int argc, char *argv[]) {
	LL_element *queryObject = NULL, *job = NULL, *step = NULL;
	LL_element *node = NULL, *task = NULL, *task_instance = NULL;
	int i, rc, obj_count, err_code, ll_master_task, job_step_count;
	char *ll_step_id= NULL, *job_step_list[2], *task_machine_name = NULL;
	int i_value32, count, ll_task_info_count;
	char *schedd_host_name = NULL, *ptr;
	LL_TASK_INFO  *ll_task_info;
	int dash_s_option = 0;
	char *tmp_buffer;
	int  tmp_buffer_size;
	int  step_mode;

	if (argc > 1) {
		if (strcmp(argv[1], "-s") == 0) {
			dash_s_option = 1;
		}
	}

	/* Get the step ID from LOADL_STEP_ID environment variable. */
	ll_step_id = getenv("LOADL_STEP_ID");
	if (!ll_step_id) {
		fprintf(stderr, "Unable to determine the job step ID: LOADL_STEP_ID env. variable is not defined.\n");
		exit(2);
	}

	job_step_list[0] = ll_step_id;
	job_step_list[1] = NULL;

	/* STEP 1: Get Job object from Central Manager to find out the name of the Schedd */
	/* daemon that handles this job. In a Multicluster environment we can not get     */
	/* the schedd name from the job step id.                                          */

	/* Initialize the LL API. Specify that query type is JOBS. */
	queryObject = ll_query(JOBS);
	if (!queryObject) {
		fprintf(stderr, "Query JOBS Error: ll_query() returns NULL.\n");
		exit(2);
	}

	/* Specify that this is a QUERY_STEPID type of query. */
	rc = ll_set_request(queryObject, QUERY_STEPID, job_step_list, ALL_DATA);
	if (rc) {
		fprintf(stderr, "ll_set_request() for QUERY_STEPID Error. RC = %d.\n", rc);
		exit(2);
	}

	/* Get a Job object from LoadL_schedd that contains the relevant job step. */
	job = ll_get_objs(queryObject, LL_CM, NULL, &obj_count, &err_code);
	if (!job) {
		fprintf(stderr, "ll_get_objs() returns NULL. Error code = %d\n", err_code);
		exit(2);
	}

	if (obj_count != 1) {  /* Only 1 Job object is expected. */
		fprintf(stderr, "ll_get_objs() Error: An unexpected number of job object count is returned.\n");
		exit(2);
	}

	rc = ll_get_data(job, LL_JobSchedd, &schedd_host_name);
	if (rc) ll_get_data_error("LL_JobSchedd", rc);
	if (schedd_host_name != NULL) {
		job_step_list[0] = ll_step_id;
		job_step_list[1] = NULL;
	} else {
		fprintf(stderr, "ll_get_objs() Error: Could not determine managing schedd for job %s.\n",job_step_list[0]);
		exit(2);
	}
	ll_free_objs(queryObject);
	ll_deallocate(queryObject);


	/* STEP 2: Get Job object from Schedd that manages this job step.   */
	/* Only schedd query gives us all the relevant task instance info.  */

	/* Initialize the LL API. Specify that query type is JOBS. */
	queryObject = ll_query(JOBS);
	if (!queryObject) {
		fprintf(stderr, "Query JOBS Error: ll_query() returns NULL.\n");
		exit(2);
	}

	/* Specify that this is a QUERY_STEPID type of query. */
	rc = ll_set_request(queryObject, QUERY_STEPID, job_step_list, ALL_DATA);
	if (rc) {
		fprintf(stderr, "ll_set_request() for QUERY_STEPID Error. RC = %d.\n", rc);
		exit(2);
	}

	/* Get a Job object from LoadL_schedd that contains the relevant job step. */
	job = ll_get_objs(queryObject, LL_SCHEDD, schedd_host_name, &obj_count, &err_code);
	if (!job) {
		fprintf(stderr, "ll_get_objs() returns NULL. Error code = %d\n", err_code);
		exit(2);
	}

	if (obj_count != 1) {  /* Only 1 Job object is expected. */
		fprintf(stderr, "ll_get_objs() Error: An unexpected number of job object count is returned.\n");
		exit(2);
	}

	rc = ll_get_data(job, LL_JobStepCount, &job_step_count);
	if (rc) ll_get_data_error("LL_JobStepCount", rc);
	if (job_step_count != 1) { /* Only 1 Job Step object is expected. */
		fprintf(stderr, "ll_get_data() Error: An unexpected number of job step count is returned.\n");
		exit(2);
	}

	step = NULL;
	rc = ll_get_data(job, LL_JobGetFirstStep, &step);
	if (rc) ll_get_data_error("LL_JobGetFirstStep", rc);
	if (!step) {
		fprintf(stderr, "ll_get_data() Error: Unable to obtain Job Step information.\n");
		exit(2);
	}

	step_mode = -1;
	rc = ll_get_data(step, LL_StepParallelMode, &step_mode);
	if (rc) ll_get_data_error("LL_StepParallelMode", rc);

	/* Serial job step: step_mode == 0; Parallel: step_mode == 1; Others: 2, 3, 4. */    

	if ((step_mode != 0) && (step_mode != 1)) {
		fprintf(stderr, "This program supports only Serial and Parallel job types. PVM, NQS, and Blue Gene jobs are not supported.\n");
		exit(2);
	}

	if (step_mode == 0) {  /* Serial Job */
		node = NULL;
		rc = ll_get_data(step, LL_StepGetFirstNode, &node);
		if (rc) ll_get_data_error("LL_StepGetFirstNode", rc);
		task = NULL;
		rc = ll_get_data(node, LL_NodeGetFirstTask, &task);
		if (rc) ll_get_data_error("LL_NodeGetFirstTask", rc);
		task_instance = NULL;
		rc = ll_get_data(task, LL_TaskGetFirstTaskInstance, &task_instance);
		if (rc) ll_get_data_error("LL_TaskGetFirstTaskInstance", rc);
		task_machine_name = NULL;
		rc = ll_get_data(task_instance, LL_TaskInstanceMachineName, &task_machine_name);
		if (rc) ll_get_data_error("LL_TaskInstanceMachineName", rc);
		if (task_machine_name) {
			if (dash_s_option == 0) {
				fprintf(stdout, "%s\n", task_machine_name);
			} else {
				fprintf(stdout, "%s", task_machine_name);
			}
		}
		ll_free_objs(queryObject);
		ll_deallocate(queryObject);

		if (task_machine_name) {
			return (0);
		} else {
			return (1);
		}
	}

	/* Parallel Jobs */
	ll_task_info_array = (LL_TASK_INFO  **) malloc(ll_task_info_array_size * sizeof(LL_TASK_INFO  *));
	if (!ll_task_info_array) ll_out_of_memory();

	node = NULL;
	rc = ll_get_data(step, LL_StepGetFirstNode, &node);
	if (rc) ll_get_data_error("LL_StepGetFirstNode", rc);
	ll_task_info_count = 0;

	while(node) {     /* Loop through the "Node" objects. */
		task = NULL;
		rc = ll_get_data(node, LL_NodeGetFirstTask, &task);
		if (rc) ll_get_data_error("LL_NodeGetFirstTask", rc);

		while(task) {  /* Loop through the "Task" objects. */
			ll_master_task = 0;
			rc = ll_get_data(task, LL_TaskIsMaster, &ll_master_task);
			if (rc) ll_get_data_error("LL_TaskIsMaster", rc);

			/* The "master task" Task object is a LoadLeveler abstraction and is not relevant here. */
			/* Look at only Task objects that are not "master". */
			if (!ll_master_task) {
				task_instance = NULL;
				rc = ll_get_data(task, LL_TaskGetFirstTaskInstance, &task_instance);
				if (rc) ll_get_data_error("LL_TaskGetFirstTaskInstance", rc);

				while (task_instance) {  /* Loop through the "Task Instance" objects. */
					task_machine_name = NULL;
					rc = ll_get_data(task_instance, LL_TaskInstanceMachineName, &task_machine_name);
					if (rc) ll_get_data_error("LL_TaskInstanceMachineName", rc);
					else {
						if (task_machine_name) {
							if (ll_task_info_count > (ll_task_info_array_size -1)) {
								ll_task_info_array_size += LL_TASK_INFO_ARRAY_SIZE_INCREMENT;
								ll_task_info_array = (LL_TASK_INFO  **) realloc(ll_task_info_array,
								                     ll_task_info_array_size * sizeof(LL_TASK_INFO  *));
								if (!ll_task_info_array) ll_out_of_memory();
							}
							/* Store machine name/task Instance ID in a LL_TASK_INFO structure. */
							ll_task_info = (LL_TASK_INFO *) malloc(sizeof(LL_TASK_INFO));
							if (!ll_task_info) ll_out_of_memory();
							ll_task_info->task_instance_machine_name = strdup(task_machine_name);
							free(task_machine_name);
							rc = ll_get_data(task_instance, LL_TaskInstanceTaskID, &i_value32);
							if (rc) ll_get_data_error("LL_TaskInstanceTaskID", rc);
							ll_task_info->task_instance_id = i_value32;
							ll_task_info_array[ll_task_info_count] = ll_task_info;
							ll_task_info_count++;
						}
					}
					task_instance = NULL;
					rc = ll_get_data(task, LL_TaskGetNextTaskInstance, &task_instance);
					if (rc) ll_get_data_error("LL_TaskGetNextTaskInstance", rc);
				}
			}
			task = NULL;
			rc = ll_get_data(node, LL_NodeGetNextTask, &task);
			if (rc) ll_get_data_error("LL_NodeGetNextTask", rc);
		}
		node = NULL;
		rc = ll_get_data(step, LL_StepGetNextNode, &node);
		if (rc) ll_get_data_error("LL_StepGetNextNode", rc);
	}

	if (ll_task_info_count > 0) {
		/* Sort the array of pointers to LL_TASK_INFO structures by task instance ID */
		qsort((void *) ll_task_info_array, ll_task_info_count, sizeof(LL_TASK_INFO *), ll_task_info_compare);

		if (dash_s_option == 0) {
			/* Write sorted machine list to standard output. One line per machine. */
			for (i = 0; i < ll_task_info_count; i++) {
				fprintf(stdout, "%s\n", ll_task_info_array[i]->task_instance_machine_name);
			}
		} else {
			/* If -s option specified, write as a single line (no new line at the end). */
			tmp_buffer_size = 0;
			for (i = 0; i < ll_task_info_count; i++) {
				tmp_buffer_size += strlen(ll_task_info_array[i]->task_instance_machine_name) + 1;
			}
			if ((tmp_buffer = (char *) malloc(tmp_buffer_size)) == NULL) ll_out_of_memory();
			bzero(tmp_buffer, tmp_buffer_size);
			for (i = 0; i < ll_task_info_count; i++) {
				strcat(tmp_buffer, ll_task_info_array[i]->task_instance_machine_name);
				if ( i < (ll_task_info_count -1)) {
					strcat(tmp_buffer, " ");
				}
			}
			fprintf(stdout, "%s", tmp_buffer); /* Single line. (no new line at the end). */
		}
	}

	ll_free_objs(queryObject);
	ll_deallocate(queryObject);
	if (ll_task_info_count < 1) return (1);
	return (0);
}

int
ll_task_info_compare(const void *p1, const void *p2) {
	LL_TASK_INFO **ptr1, **ptr2;
	ptr1 = (LL_TASK_INFO **) p1;
	ptr2 = (LL_TASK_INFO **) p2;
	if ((*ptr1)->task_instance_id < (*ptr2)->task_instance_id) return (-1);
	if ((*ptr1)->task_instance_id > (*ptr2)->task_instance_id) return (+1);
	return (0);
}

void
ll_get_data_error(const char *ptr, int rc) {
	fprintf(stderr, "Error: ll_get_data() for %s failed. Return Code = %d\n", ptr, rc);
	exit(2);
}

void
ll_out_of_memory(void)
{
	fprintf(stderr, "Error: Unable to allocate memory.\n");
	exit(2);
}

