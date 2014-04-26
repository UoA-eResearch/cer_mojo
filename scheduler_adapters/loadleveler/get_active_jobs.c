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
    fprintf(stderr,"hello ");
    job = ll_get_objs(query_elem,LL_CM,NULL,&job_count,&rc);
    fprintf(stderr,"world");
    if(rc<0) {
      show_getobjs_rc(rc);
    } else {
      printf("Number of Jobs = %d\n", job_count);
      i = 0;
      while(job!=NULL) {
        printf("------------------------------------------------------\n");
        show_LL_job(job);
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


void show_LL_job(LL_element *job) {
  int i;
  int max_mach_count;
  int min_mach_count;
  int parallel_threads;
  LL_element * step;
  LL_element * node;
  LL_element * task;
  LL_element * machine;
  LL_element * resource_request;
  LL_element * credential;
  time_t tBuffer;
  char * pcBuffer;
  int iBuffer;
  int64_t i64Buffer;

  // owner is part of the job credential
  ll_get_data(job, LL_JobCredential, &credential);
  GET_DATA(credential,LL_CredentialUserName,pcBuffer,"Owner = %s\n");
  free(pcBuffer);

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

    GET_DATA(step,LL_StepState,iBuffer,"State = %d\n");
    GET_DATA(step,LL_StepTaskAffinity,pcBuffer,"Task Affinity = %s\n");
    GET_DATA(step,LL_StepID,pcBuffer,"Step ID = %s\n");
    free(pcBuffer);
    GET_TIME_DATA(step,LL_StepDispatchTime,tBuffer,"Dispatch Time = %s\n");
    GET_DATA(step,LL_StepName,pcBuffer,"Name = %s\n");
    free(pcBuffer);
    GET_DATA(step,LL_StepJobClass,pcBuffer,"Class = %s\n");
    free(pcBuffer);
    printf("Hard Limits:\n");
    GET_DATA(step,LL_StepWallClockLimitHard,iBuffer,"\tWallClock     = %d\n");

    max_mach_count=0;
    min_mach_count=0;
    parallel_threads= 0;
    ll_get_data(step,LL_StepGetFirstNode,&node);
    while(node!=NULL) {
      ll_get_data(node,LL_NodeInitiatorCount,&iBuffer);
      parallel_threads += iBuffer;
      ll_get_data(node,LL_NodeGetFirstTask,&task);
      while(task!=NULL) {
        //GET_DATA(task,LL_TaskInstanceMachineName,pcBuffer,"Machine Name = %s\n");
        // TODO: ignore master task!!!
        GET_DATA(task,LL_TaskTaskInstanceCount,iBuffer,"Task Instance Count = %d\n");
        ll_get_data(task,LL_TaskGetFirstResourceRequirement,&resource_request);
        while(resource_request!=NULL) {
          ll_get_data(resource_request,LL_ResourceRequirementName,&pcBuffer);
          ll_get_data(resource_request,LL_ResourceRequirementValue,&iBuffer);
          printf("%s = %d\n", pcBuffer, iBuffer);
          ll_get_data(task,LL_TaskGetNextResourceRequirement,&resource_request);
        }
        ll_get_data(node,LL_NodeGetNextTask,&task);
      } 
      ll_get_data(node,LL_NodeMaxInstances,&iBuffer);
      max_mach_count += iBuffer;
      ll_get_data(node,LL_NodeMinInstances,&iBuffer);
      min_mach_count += iBuffer;
      ll_get_data(step,LL_StepGetNextNode,&node);
    }
    printf("Parallel threads: %d\n",parallel_threads);
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
