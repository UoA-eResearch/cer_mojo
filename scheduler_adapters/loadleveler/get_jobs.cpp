/*
 * Get number of active and idle jobs for each user
 * who is currently running a job on the cluster
 */

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
    Jobs() {}
    char status;
    string username;
    string queue;
    int req_cores;
    string queued_time;
    string start_time;
    string master_node;
};


typedef std::map<std::string,Jobs> JOBSLIST;

void process_job(LL_element *, JOBSLIST&, string);
string get_stepid(LL_element *);
string get_username(LL_element *);
string get_queue(LL_element *);
int get_num_threads(LL_element *);
int get_num_tasks(LL_element *);
int get_num_cores(LL_element *);
int figure_out_cores(LL_element *step);
string get_queued_time(LL_element *);
string get_start_time(LL_element *);
string get_master_node(LL_element *);

int main(int argc, char **argv) {
  int rc;
  int count;
  LL_element * query_elem;
  LL_element * job;
  JOBSLIST jobs;
  string user("");

  if (argc == 2) {
    user = string(argv[1]);
  } 

  if ((query_elem = ll_query(JOBS)) == NULL) {
    fprintf(stderr,"Unable to obtain query element\n");
    exit(1);
  }

  rc=ll_set_request(query_elem,QUERY_ALL,NULL,ALL_DATA);
  if(rc<0) {
    fprintf(stderr,"ll_set_request() failed");
    exit(1);
  } 

  job = ll_get_objs(query_elem,LL_CM,NULL,&count,&rc);
  if(rc<0) {
    fprintf(stderr,"ll_get_objs() failed");
    exit(1);
  } 

  while(job!=NULL) {
    process_job(job, jobs, user);
    job = ll_next_obj(query_elem);
  }

  for(JOBSLIST::iterator ii=jobs.begin(); ii!=jobs.end(); ii++) {
    cout << ii->first << "|"
         << ii->second.status << "|" 
         << ii->second.username << "|" 
         << ii->second.queue << "|" 
         << ii->second.req_cores << "|" 
         << ii->second.master_node << "|" 
         << ii->second.queued_time << "|"
         << ii->second.start_time << endl;
  } 

  ll_free_objs(query_elem); 
  ll_deallocate(query_elem); 
  return 0;
}


void process_job(LL_element *job, JOBSLIST& jobs, string user) {
  LL_element * step;
  LL_element * credential;
  LL_element * node;
  char * pcBuffer;
  int iBuffer;
  int numthreads;
  int rc;

  string queued_time = get_queued_time(job);

  ll_get_data(job,LL_JobGetFirstStep,&step);

  while(step!=NULL) {
    ll_get_data(step,LL_StepState,&iBuffer);
    string id = get_stepid(step);
    string tmp_user = get_username(job);
    if (!user.empty() && tmp_user.compare(user) != 0) {
      ll_get_data(job,LL_JobGetNextStep,&step);
      continue;
    }
    jobs[id].username = tmp_user;
    jobs[id].queue = get_queue(step);
    jobs[id].req_cores = get_num_cores(step);
    jobs[id].queued_time = queued_time;
    if (STATE_RUNNING == iBuffer) {
      jobs[id].status = 'R';
      jobs[id].start_time = get_start_time(step);
      jobs[id].master_node = get_master_node(step);
    } else {
      jobs[id].status = 'I';
    }
    ll_get_data(job,LL_JobGetNextStep,&step);
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
    while(node) {  /* Loop through the "Task" objects. */
      int ll_master_task = 0;
      ll_get_data(node, LL_NodeGetFirstTask, &task);
      while (task) {
        ll_get_data(task, LL_TaskIsMaster, &ll_master_task);
        if (!ll_master_task) {
          LL_element * task_instance = NULL;
          ll_get_data(task, LL_TaskGetFirstTaskInstance, &task_instance);
          while (task_instance) {  /* Loop through the "Task Instance" objects. */
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

  if (numcores == 0) {
    numcores = figure_out_cores(step);
  }
  return numcores;
}

int figure_out_cores(LL_element *step) {
    int rc;
    int cores=0;

    rc=ll_get_data(step,LL_StepTotalTasksRequested,&cores);

    if(rc!=0 || !cores) {
        //not total tasks, try figure it out by node
        int nodes=0,tasks=0;
        cores=0;

        rc=ll_get_data(step,LL_StepTaskInstanceCount,&tasks);

        if(tasks && rc==0) {
           return (tasks>1?tasks-1:tasks); //Why it returns tasks+1 beats me!
        }

        tasks=0;
        rc=ll_get_data(step,LL_StepTotalNodesRequested,&nodes);
        if(rc!=0) {
            nodes=1;
        }
        if(nodes>10000) {
           nodes=1;
        }
        rc=ll_get_data(step,LL_StepTasksPerNodeRequested,&tasks);
        if(rc==0) {
            cores=nodes*tasks;
        }
    }

    if(!cores) {
        cores=1;
    }
    if(cores>300000) {
        cores=1;
    }

    return cores;
}
