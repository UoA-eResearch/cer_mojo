#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <iostream>
#include <sstream>
#include <map>
#include <utility>
#include "llapi.h"

using namespace std;

struct Jobs {
  //Job() {}
  string status;
  string jobtype;
  string username;
  string queue;
  string job_dir;
  int req_cores;
  int req_mem_mb;
  int req_vmem_mb;
  string req_walltime;
  string used_walltime;
  string queued_time;
  string start_time;
  string master_node;
  string nodes;
};

typedef std::map<std::string,Jobs> JOBSLIST;

void process_job(LL_element *, JOBSLIST&);
string get_stepid(LL_element *);
string get_status(LL_element *);
string get_username(LL_element *);
string get_queue(LL_element *);
string get_jobtype(LL_element *);
string get_jobdir(LL_element *);
int get_req_cores(LL_element *);
int get_req_mem_mb(LL_element *);
int get_req_vmem_mb(LL_element *);
string get_req_walltime(LL_element *);
string get_used_walltime(LL_element *);
string get_queued_time(LL_element *);
string get_start_time(LL_element *);
string get_master_node(LL_element *);
string get_nodes(LL_element *);
int get_num_cores(LL_element *);
int get_num_tasks(LL_element *);


int main(int argc, char **argv) {
  int rc;
  int count;
  int obj_count;
  int err_code;
  LL_element * queryObject = NULL;
  LL_element * job = NULL;
  char ** job_step_list = NULL;
  JOBSLIST jobs;

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

  string s("peter");
  while (job) {
    cerr << "aaa" << endl;
    jobs[s].username = s;
    process_job(job, jobs);
    cerr << "bbb" << endl;
    job = ll_next_obj(queryObject); 
    cerr << "ccc" << endl;
  }

  for(JOBSLIST::iterator ii=jobs.begin(); ii!=jobs.end(); ii++) {
    cout << ii->first << "|"
         << ii->second.username << "|"
         << endl;
/*
         << ii->second.status << "|" 
         << ii->second.queue << "|" 
         << ii->second.req_cores << "|" 
         << ii->second.master_node << "|" 
         << ii->second.queued_time << "|"
         << ii->second.start_time << endl;
*/
  } 

  cerr << "ddd" << endl;
  //ll_free_objs(queryObject); 
  cerr << "eee" << endl;
  //ll_deallocate(queryObject); 
  cerr << "fff" << endl;
  return 0;
}

void process_job(LL_element *job, JOBSLIST& jobs) {
  LL_element * step;
  char * pcBuffer;
  int iBuffer;
  string id;

  ll_get_data(job,LL_JobGetFirstStep,&step);
  while(step) {
    cerr << get_username(job) << endl;
/*
    jobs[id].username = get_username(job);
    string id = get_stepid(step);
    jobs[id].queued_time = get_queued_time(job);
    jobs[id].status = get_status(step);
    jobs[id].queue = get_queue(step);
    jobs[id].req_cores = get_num_cores(step);
    jobs[id].start_time = get_start_time(step);
    jobs[id].master_node = get_master_node(step);
    jobs[id].username = get_username(job);
*/
    cerr << "111" << endl;
    ll_get_data(job,LL_JobGetNextStep,&step);
    cerr << "222" << endl;
  }
}

string get_username(LL_element * job) {
  LL_element * credential;
  char *tmp;
  ll_get_data(job, LL_JobCredential, &credential);
  ll_get_data(credential,LL_CredentialUserName,&tmp);
  string username(tmp);
  free(tmp);
  return username;
}

/*
string get_status(LL_element * step) {
  int iBuffer;
  string status = "N/A";
  ll_get_data(step,LL_StepState,&iBuffer);
  switch(iBuffer) {
    case STATE_IDLE:
      status = string("I");
      break;
    case STATE_RUNNING:
      status = string("R");
      break;
    case STATE_NOTQUEUED:
      status = string("NQ");
      break;
  }
  return status;
}

string get_stepid(LL_element * step) {
  char *tmp;
  ll_get_data(step, LL_StepID, &tmp);
  string id(tmp);
  free(tmp);
  return id;
}

string get_queue(LL_element * step) {
  char *tmp;
  ll_get_data(step, LL_StepJobClass, &tmp);
  string queue(tmp);
  free(tmp);
  return queue;
}

string get_master_node(LL_element * step) {
  LL_element * task;
  LL_element * task_instance;
  char *tmp;
  ll_get_data(step, LL_StepGetMasterTask, &task);
  ll_get_data(task, LL_TaskGetFirstTaskInstance, &task_instance);
  ll_get_data(task_instance, LL_TaskInstanceMachineName, &tmp);
  string machine(tmp);
  free(tmp);
  return machine;
}

string get_queued_time(LL_element * job) {
  time_t time;
  char buff[20];
  ll_get_data(job,LL_JobSubmitTime,&time);
  strftime(buff, 20, "%Y-%m-%d %H:%M:%S", localtime(&time));
  return string(buff);
}

string get_start_time(LL_element * step) {
  time_t time;
  char buff[20];
  ll_get_data(step,LL_StepDispatchTime,&time);
  strftime(buff, 20, "%Y-%m-%d %H:%M:%S", localtime(&time));
  return string(buff);
}

int get_num_threads(LL_element * step) {
  char *aff;
  int cores = 1;
  ll_get_data(step,LL_StepTaskAffinity, &aff);
  if (aff != NULL) {
    string affstring(aff);
    if (affstring.find("cpu(") != string::npos) {
      int pos1 = affstring.find("(")+1;
      int pos2 = affstring.find(")");
      stringstream(affstring.substr(pos1, pos2-pos1)) >> cores;
    } 
  }
  return cores;
}    

int get_num_cores(LL_element * step) {
  int numcores = 0;
  int step_mode = -1;
  int rc;
  ll_get_data(step, LL_StepParallelMode, &step_mode);
  if (step_mode == 0) {
    numcores = get_num_threads(step);
  } else {
    LL_element * node;
    LL_element * task;
    LL_element * task_instance;
    ll_get_data(step, LL_StepGetFirstNode, &node);
    while(node) { 
      int ll_master_task = 0;
      ll_get_data(node, LL_NodeGetFirstTask, &task);
      while (task) {
        ll_get_data(task, LL_TaskIsMaster, &ll_master_task);
        if (!ll_master_task) {
          LL_element * task_instance = NULL;
          ll_get_data(task, LL_TaskGetFirstTaskInstance, &task_instance);
          while (task_instance) { 
            int * cpulist;
            ll_get_data(task_instance, LL_TaskInstanceCpuList, &cpulist);
            for (int i=0; i<sizeof(cpulist); i++) {
              if (cpulist[i] < 0) {
                break;
              } else {
                numcores += 1; 
              }
            }
            free(cpulist);
            ll_get_data(task, LL_TaskGetNextTaskInstance, &task_instance);
          }
        }
        ll_get_data(node, LL_NodeGetNextTask, &task);
      }
      ll_get_data(step, LL_StepGetNextNode, &node);
    }
  }
  return numcores;
}

*/
