#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <iostream>
#include <sstream>
#include <map>
#include <utility>
#include <time.h>
#include "llapi.h"

using namespace std;

struct ResourceTuple {
  ResourceTuple():cores(0),mem(0),vmem(0) {}
  int cores;
  int mem;
  int vmem;
};

struct MyJob {
  MyJob() {}
  string status;
  string jobtype;
  string username;
  string queue;
  string job_dir;
  int req_cores;
  pair<int,int> req_mem_mb;
  string req_walltime;
  string used_walltime;
  int queued_time;
  int start_time;
  string master_node;
  string working_dir;
  map<string,ResourceTuple> geometry;
};

typedef std::map<std::string,MyJob> JOBSLIST;
typedef std::map<string,ResourceTuple> JOBGEOMETRY;

void process_job(LL_element *, JOBSLIST &);
string get_stepid(LL_element *);
string get_status(LL_element *);
string get_username(LL_element *);
string get_queue(LL_element *);
string get_jobtype(LL_element *);
string get_jobdir(LL_element *);
int get_req_cores(LL_element *);
pair<int,int> get_req_mem_mb(LL_element *);
string get_req_walltime(LL_element *);
string get_used_walltime(LL_element *);
int get_queued_time(LL_element *);
int get_start_time(LL_element *);
string get_master_node(LL_element *);
string get_working_dir(LL_element *);
string get_nodes(LL_element *);
int get_num_cores(LL_element *);
int get_num_tasks(LL_element *);
string format_duration(int);
JOBGEOMETRY get_geometry(LL_element *);


int main(int argc, char **argv) {
  int rc;
  int count;
  int obj_count;
  int err_code;
  LL_element * queryObject = NULL;
  LL_element * job = NULL;
  char ** job_step_list = NULL;
  JOBSLIST myjobs;

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

  while (job) {
    process_job(job, myjobs);
    job = ll_next_obj(queryObject); 
  }

  for(JOBSLIST::iterator ii=myjobs.begin(); ii!=myjobs.end(); ii++) {
    cout << ii->first << "|"
         << ii->second.username << "|"
         << ii->second.status << "|" 
         << ii->second.queue << "|" 
         << ii->second.req_cores << "|" 
         << ii->second.req_mem_mb.first << "|"
         << ii->second.req_mem_mb.second << "|"
         << ii->second.master_node << "|" 
         << ii->second.working_dir << "|" 
         << ii->second.queued_time << "|"
         << ii->second.start_time << "|"
         << ii->second.req_walltime << "|"
         << ii->second.used_walltime << "|";
    int count = 0;
    for (JOBGEOMETRY::iterator ij=ii->second.geometry.begin(); ij!=ii->second.geometry.end(); ij++) {
      if (count++ > 0) {
        cout << ",";
      }
      cout << ij->first << ":" << ij->second.cores << ":" << ij->second.mem << ":" << ij->second.vmem;
    }
    cout << endl;
  } 

  //ll_free_objs(queryObject); 
  //ll_deallocate(queryObject); 
  return 0;
}

void process_job(LL_element *job, JOBSLIST& myjobs) {
  LL_element * step;
  char * pcBuffer;
  int iBuffer;

  ll_get_data(job,LL_JobGetFirstStep,&step);
  while(step) {
    string id = get_stepid(step);
    myjobs[id].username = get_username(job);
    myjobs[id].status = get_status(step);
    myjobs[id].queue = get_queue(step);
    myjobs[id].req_cores = get_num_cores(step);
    myjobs[id].req_mem_mb = get_req_mem_mb(step);
    myjobs[id].queued_time = get_queued_time(job);
    myjobs[id].master_node = get_master_node(step);
    myjobs[id].working_dir = get_working_dir(step);
    myjobs[id].req_walltime = get_req_walltime(step);
    if (myjobs[id].status.compare("Running") == 0) {
      myjobs[id].start_time = get_start_time(step);
      myjobs[id].used_walltime = get_used_walltime(step);
      myjobs[id].geometry = get_geometry(step);
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

string get_working_dir(LL_element * step) {
  char *tmp;
  ll_get_data(step, LL_StepIwd, &tmp);
  string dir(tmp);
  return dir;
}

string get_stepid(LL_element * step) {
  char *tmp;
  ll_get_data(step, LL_StepID, &tmp);
  string id(tmp);
  free(tmp);
  return id;
}

string get_status(LL_element * step) {
  int iBuffer;
  string status = "N/A";
  ll_get_data(step,LL_StepState,&iBuffer);
  switch(iBuffer) {
    case STATE_IDLE:
      status = string("Idle");
      break;
    case STATE_RUNNING:
      status = string("Running");
      break;
    case STATE_NOTQUEUED:
      status = string("NotQueued");
      break;
  }
  return status;
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
  char *tmp = NULL;
  ll_get_data(step, LL_StepGetMasterTask, &task);
  ll_get_data(task, LL_TaskGetFirstTaskInstance, &task_instance);
  ll_get_data(task_instance, LL_TaskInstanceMachineName, &tmp);
  if (tmp) {
    string machine(tmp);
    free(tmp);
    return machine;
  }
  return string("");
}

int get_queued_time(LL_element * job) {
  time_t time;
  ll_get_data(job,LL_JobSubmitTime,&time);
  return time;
}

int get_start_time(LL_element * step) {
  time_t time;
  ll_get_data(step,LL_StepDispatchTime,&time);
  return time;
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
              if (cpulist[i] < 0) { // -1 is terminator
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

pair<int,int> get_req_mem_mb(LL_element *step) {
  LL_element * node;
  LL_element * task;
  LL_element * rr;
  int step_mode;
  string mem_name("ConsumableMemory");
  string vmem_name("ConsumableVirtualMemory");
  int mem=-1;
  int vmem=-1;

  ll_get_data(step, LL_StepParallelMode, &step_mode);
  ll_get_data(step, LL_StepGetFirstNode, &node);
  while(node) {
    int ll_master_task = 0;
    ll_get_data(node, LL_NodeGetFirstTask, &task);
    while (task) {
      ll_get_data(task, LL_TaskIsMaster, &ll_master_task);
      LL_element * rr = NULL;
      if (step_mode == 0 && ll_master_task) { // Serial job
        ll_get_data(task, LL_TaskGetFirstResourceRequirement, &rr);
      } else if (step_mode != 0 && !ll_master_task) { // Parallel job
        ll_get_data(task, LL_TaskGetFirstResourceRequirement, &rr);
      } else {
        ll_get_data(node, LL_NodeGetNextTask, &task);
        continue;
      }
      while (rr) {
        char * rrname;
        int rrvalue;
        ll_get_data(rr,LL_ResourceRequirementName, &rrname);
        if (mem_name.compare(rrname) == 0) {
          ll_get_data(rr,LL_ResourceRequirementValue, &mem);
        } else if (vmem_name.compare(rrname) == 0) {
          ll_get_data(rr,LL_ResourceRequirementValue, &vmem);
        }
        ll_get_data(task, LL_TaskGetNextResourceRequirement, &rr);
      }
      ll_get_data(node, LL_NodeGetNextTask, &task);
    }
    ll_get_data(step, LL_StepGetNextNode, &node);
  }
  return make_pair(mem, vmem);
}

int get_num_tasks(LL_element * step) {
  int numtasks = 0;
  int rc;
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
        ll_get_data(task, LL_TaskTaskInstanceCount, &numtasks);
        return numtasks;
      }
      ll_get_data(node, LL_NodeGetNextTask, &task);
    }
    ll_get_data(step, LL_StepGetNextNode, &node);
  }
  return numtasks;
}

JOBGEOMETRY get_geometry(LL_element * step) {
  JOBGEOMETRY geometry;
  int numcores = 0;
  int step_mode = -1;
  int rc;
  char * machine_name;
  pair<int,int> mem = get_req_mem_mb(step);

  ll_get_data(step, LL_StepParallelMode, &step_mode);

  if (step_mode == 0) {
    numcores = get_num_threads(step);
    LL_element * machine;
    ll_get_data(step, LL_StepGetFirstMachine, &machine);
    ll_get_data(machine, LL_MachineName, &machine_name);
    string mname(machine_name);
    geometry[mname].cores = numcores;
    geometry[mname].mem = mem.first;
    geometry[mname].vmem = mem.second;
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
            char * machine_name;
            ll_get_data(task_instance,LL_TaskInstanceMachineName, &machine_name);
            ll_get_data(task_instance, LL_TaskInstanceCpuList, &cpulist);
            string mname(machine_name);
            geometry[mname].mem += mem.first;
            geometry[mname].vmem += mem.second;
            for (int i=0; i<sizeof(cpulist); i++) {
              if (cpulist[i] < 0) { // -1 is terminator
                break;
              } else {
                geometry[mname].cores += 1;
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

  return geometry;
}

string get_req_walltime(LL_element * step) {
  int walltime_sec = 0;
  ll_get_data(step, LL_StepWallClockLimitHard, &walltime_sec);
  return format_duration(walltime_sec);
}

string get_used_walltime(LL_element * step) {
  int start_time = get_start_time(step);
  int now = time(0);
  return format_duration(now-start_time);
}

string format_duration(int sec) {
  int tmp = sec;
  ostringstream oss;
  int days = tmp/86400;
  oss << days << "+";
  tmp -= 86400 * days;
  int hours =  tmp/3600;
  if (hours < 10) {
    oss << "0";
  }
  oss << hours << ":";
  tmp -= 3600 * hours;
  int minutes = tmp/60;
  if (minutes < 10) {
    oss << "0";
  }
  oss << minutes << ":";
  tmp -= 60 * minutes;
  int seconds = tmp;
  if (seconds < 10) {
    oss << "0";
  }
  oss << seconds;
  return oss.str();
}

