/*
 * Get number of active and idle jobs for each user
 * who is currently running a job on the cluster
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <iostream>
#include <map>
#include <utility>
#include "llapi.h"

using namespace std;

struct Jobs {
    Jobs():active(0),idle(0),nq(0) {}
    unsigned int active;
    unsigned int idle;
    unsigned long nq;
};


typedef std::map<std::string,Jobs> JOBSLIST;

void process_job(LL_element *, JOBSLIST&);

int main(int argc, char **argv) {
  int rc;
  int count;
  LL_element * query_elem;
  LL_element * job;
  JOBSLIST jobs;

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
    process_job(job, jobs);
    job = ll_next_obj(query_elem);
  }

  for(JOBSLIST::iterator ii=jobs.begin(); ii!=jobs.end(); ii++) {
    cout << ii->first << "|" << ii->second.active << "|" << ii->second.idle << "|" << ii->second.nq << endl;
  } 

  ll_free_objs(query_elem); 
  ll_deallocate(query_elem); 
  return 0;
}


void process_job(LL_element *job, JOBSLIST& jobs) {
  LL_element * step;
  LL_element * credential;
  char * pcBuffer;
  int iBuffer;

  ll_get_data(job,LL_JobGetFirstStep,&step);
  while(step!=NULL) {
    ll_get_data(step,LL_StepState,&iBuffer);
    if (STATE_IDLE == iBuffer || STATE_RUNNING == iBuffer || STATE_NOTQUEUED==iBuffer) {
      ll_get_data(job, LL_JobCredential, &credential);
      ll_get_data(credential,LL_CredentialUserName,&pcBuffer);
      string username(pcBuffer);
      free(pcBuffer);
      switch(iBuffer)
      {
           case STATE_IDLE:jobs[username].idle++;
                break;
           case STATE_RUNNING:jobs[username].active++;
                break;
           case STATE_NOTQUEUED:jobs[username].nq++;
                break;
      }
    }
    ll_get_data(job,LL_JobGetNextStep,&step);
  }  
}
