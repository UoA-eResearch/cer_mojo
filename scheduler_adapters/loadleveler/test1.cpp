#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <iostream>
#include "llapi.h"

using namespace std;

int main(int argc, char *argv[]) {
  LL_element *queryObject = NULL, *job = NULL, *step = NULL;
  LL_element *node = NULL, *task = NULL, *task_instance = NULL;
  int i, rc, obj_count, err_code, ll_master_task, job_step_count;
  char *ll_step_id= NULL, **job_step_list, *task_machine_name = NULL;
  int i_value32, count, ll_task_info_count;
  char *schedd_host_name = NULL, *ptr;
  int dash_s_option = 0;
  char *tmp_buffer;
  int  tmp_buffer_size;
  int  step_mode;

  /* daemon that handles this job. In a Multicluster environment we can not get     */
  /* the schedd name from the job step id.                                          */

  /* Initialize the LL API. Specify that query type is JOBS. */
  queryObject = ll_query(JOBS);
  if (!queryObject) {
    fprintf(stderr, "Query JOBS Error: ll_query() returns NULL.\n");
    exit(2);
  }


   /* Set query parameters: query specific machines by name */
  job_step_list = (char **)malloc((argc+1)*sizeof(char *));
  i=0;
  for(i=0;i<argc;i++) {
    job_step_list[i] = argv[i+1];
  }
  job_step_list[i] = NULL;

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
  
 if (obj_count != (argc-1)) {  /* Only 1 Job object is expected. */
  fprintf(stderr, "ll_get_objs() Error: An unexpected number of job object count is returned.\n");
  exit(2);
 }

    cout << "done" << endl;
}

