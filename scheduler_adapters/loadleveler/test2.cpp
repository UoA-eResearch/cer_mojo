#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <iostream>
#include "llapi.h"

using namespace std;

int main(int argc, char *argv[]) {
  int rc;
  int count;
  int obj_count;
  int err_code;
  LL_element * queryObject = NULL;
  LL_element * job = NULL;
  char ** job_step_list = NULL;

  if(argc<2) {
    cerr << "Usage: " << argv[0] << " <jobid> [jobid jobid ...]" << endl;
    return -1;
  }

  /* Set query parameters: query specific machines by name */
  job_step_list = (char **)malloc((argc+1)*sizeof(char *));
  int i=0;
  for(i=0;i<argc;i++) {
    job_step_list[i] = argv[i+1];
  }
  job_step_list[i] = NULL;

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

  if (obj_count != (argc-1)) {  /* Only 1 Job object is expected. */
    fprintf(stderr, "ll_get_objs() Error: An unexpected number of job object count is returned.\n");
    exit(2);
  }

  cout << "done" << endl;
}

