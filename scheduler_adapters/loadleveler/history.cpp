#include <stdio.h>
#include <string.h>
#include <time.h>
#include <stdlib.h>
#include <llapi.h>
#include <llrapi.h>
#include "struct.h"
#include <map>
#include <string>

using namespace std;

typedef std::map<std::string,std::pair<int,unsigned long> > STEPS;

STEPS steps;

//#define USE_FULL_API 1

llr_resmgr_handle_t *rmh=NULL;

char *history_file=NULL;

unsigned long get_id(const char *jobid)
{
    char tmp[256];
    char *p;

    strcpy(tmp,jobid);
    //rely on stepid format with 2 dots
    p=strrchr(tmp,'.');
    if(!p)
        return 0;
    memmove(p,p+1,strlen(p)-1);
    p[strlen(p)-1]=0;
    p=strchr(tmp,'.');
    if(!p)
        return 0;
    return strtoul(p+1,NULL,0);
}

void print_job(const struct Job *j)
{
    char str[256];

    printf("User           : %s\n",j->user);
    printf("Job            : %s\n",j->jobid);
    printf("Job name       : %s\n",j->jobname);
    printf("Account        : %s\n",j->account);
    printf("Comment        : %s\n",j->comment);
    printf("Group          : %s\n",j->group);
    printf("Class          : %s\n",j->jobClass);
    printf("Mode           : %s\n",(j->mode?"Parallel":"Serial"));
    printf("Tasks          : %d\n",j->tasks);
    printf("Wallclock req  : %d\n",j->wallclockRequested);
    printf("Wallclock used : %d\n",j->wallclockUsed);
    printf("Status         : %d\n",j->status);
    printf("Memory         : %lld\n",j->mem);
    asctime_r(localtime(&j->submitTime),str);
    printf("Submitted      : %s",str);
    asctime_r(localtime(&j->startTime),str);
    printf("Started        : %s",str);
    asctime_r(localtime(&j->completeTime),str);
    printf("Completed      : %s",str);
}

void process_job(const struct Job *j)
{
    int i;
//    printf("replace into audit (id,jobid,jobname,jobtype,user,account,jobgroup,queue,cores,flags,status,appstatus,walltime,start,done,qtime,executable,memrequested,iwd,utilisation,nodes,processors) values ("
    printf("insert ignore into audit (id,jobid,jobname,jobtype,user,account,jobgroup,queue,cores,flags,status,appstatus,walltime,start,done,qtime,executable,memrequested,iwd,utilisation,nodes,processors) values ("
           "%lu,'%s','%s','%s','%s','%s','%s','%s',%d,%d,%d,%d,%d,%d,%d,%d,'%s',%lld,'%s',%lu,%d,'",
           get_id(j->jobid),j->jobid,j->jobname,(j->mode?"parallel":"serial"),j->user,j->account,j->group,j->jobClass,j->tasks,j->flags,j->status,j->app_status,
           j->wallclockRequested,j->startTime,j->completeTime,j->submitTime,j->exec,j->mem,j->iwd,j->exec_time,j->nodes);
    for(i=0;i<j->nodes;i++)
        printf("%s%s",(i==0?"":","),j->procs[i]);
    printf("');\n");
}


int figure_out_cores(llr_element_t *job,void *step)
{
    llr_element_t *err=NULL;
    int rc;
    int cores=0;

    rc=llr_get_data(rmh,step,LLR_StepTotalTasksRequested,&cores,&err);

    if(rc!=LLR_API_OK || !cores)
    {
        //not total tasks, try figure it out by node
        int nodes=0,tasks=0;
        cores=0;

        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepTaskInstanceCount,&tasks,&err);

        if(tasks && rc==LLR_API_OK)
        {
           return (tasks>1?tasks-1:tasks); //Why it returns tasks+1 beats me! 
        }

        tasks=0;
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepTotalNodesRequested,&nodes,&err);
        if(rc!=LLR_API_OK)
        {
            nodes=1;
        }
        if(nodes>10000)
           nodes=1;
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepTasksPerNodeRequested,&tasks,&err);
        if(rc==LLR_API_OK)
            cores=nodes*tasks;
    }

    if(!cores)
        cores=1;
    if(cores>300000)
    { 
        cores=1;
    }

    return cores;
}


#define  STR_NULL(ptr) (ptr ? ptr : "")

int64_t figure_out_memory(llr_element_t *job,void *step)
{
    llr_element_t *err=NULL;
    int rc;
    int64_t mem=0;
    LL_element *mach_usage = NULL, *disp_usage = NULL, *event_usage = NULL;
    int mach_usage_count, disp_usage_count, event_usage_count,data;
    int64_t int64_data;
    char *str_data;


    rc=llr_get_data(rmh,step,LLR_StepStepIdrss64,&mem,&err);
    if(mem)
        return mem;
    //try events now
    /* Loop through the machine usage objects. */
    /* A parallel job step run on 3 machines typically has 3 machine usage objects. */
    mach_usage_count = 0;
    rc = ll_get_data(step, LL_StepGetFirstMachUsage, &mach_usage);
    while (mach_usage) 
    {
	mach_usage_count++;
	ll_get_data(mach_usage, LL_MachUsageMachineName, &str_data);

        data=0;
	//ll_get_data(mach_usage, LL_StepWallClockUsed, &data);

	/* Loop through the dispatch usage objects. */
	/* Unless the job is restarted, there is usually 1 dispatch usage object. */
	disp_usage_count = 0;
	ll_get_data(mach_usage, LL_MachUsageGetFirstDispUsage, &disp_usage);
	while(disp_usage) 
        {
		disp_usage_count++;

		ll_get_data(disp_usage, LL_DispUsageStepUserTime64, &int64_data);
		ll_get_data(disp_usage, LL_DispUsageStepSystemTime64, &int64_data);

		/* Loop through the event usage objects. */
		/* Each dispatch typically has 2 events: "started" and "completed". */
		/* There may be other events if the LL administrator executes the command */
		/* "llctl -g capture <user event name>" while the job is running.         */
		event_usage_count = 0;
		ll_get_data(disp_usage, LL_DispUsageGetFirstEventUsage, &event_usage);
		while (event_usage) 
		{
			event_usage_count++;
			ll_get_data(event_usage, LL_EventUsageEventName, &str_data);
			ll_get_data(event_usage, LL_EventUsageStepUserTime64, &int64_data);
			ll_get_data(event_usage, LL_EventUsageStepSystemTime64, &int64_data);
                        int64_data=0;
			ll_get_data(event_usage, (LLAPI_Specification)LLR_EventUsageStepIdrss64, &int64_data);
                        mem+=int64_data;
                        int64_data=0;
			ll_get_data(event_usage, (LLAPI_Specification)LLR_EventUsageStepIsrss64, &int64_data);
                        mem+=int64_data;
                        int64_data=0;
			ll_get_data(event_usage, (LLAPI_Specification)LLR_EventUsageStepIxrss64, &int64_data);
                        mem+=int64_data;
                        int64_data=0;
			ll_get_data(event_usage, (LLAPI_Specification)LLR_EventUsageStepMaxrss64, &int64_data);
                        mem=int64_data;
			event_usage = NULL;
			ll_get_data(disp_usage, LL_DispUsageGetNextEventUsage, &event_usage);
		}
		disp_usage = NULL;
		ll_get_data(mach_usage, LL_MachUsageGetNextDispUsage, &disp_usage);
	}
	mach_usage = NULL;
	rc = ll_get_data(step, LL_StepGetNextMachUsage, &mach_usage);
    }

    return mem;
}


const char* step_state_string(llr_step_state_t s) 
{
        switch(s) 
        {
        case LLR_STATE_CANCELED:         return "STATE_CANCELED";
        case LLR_STATE_COMPLETED:        return "STATE_COMPLETED";
        case LLR_STATE_COMPLETE_PENDING: return "STATE_COMPLETE_PENDING";
        case LLR_STATE_DEFERRED:         return "STATE_DEFERRED";
        case LLR_STATE_HOLD:             return "STATE_HOLD";
        case LLR_STATE_IDLE:             return "STATE_IDLE";
        case LLR_STATE_NOTQUEUED:        return "STATE_NOTQUEUED";
        case LLR_STATE_NOTRUN:           return "STATE_NOTRUN";
        case LLR_STATE_PENDING:          return "STATE_PENDING";
        case LLR_STATE_PREEMPTED:        return "STATE_PREEMPTED";
        case LLR_STATE_PREEMPT_PENDING:  return "STATE_PREEMPT_PENDING";
        case LLR_STATE_REJECTED:         return "STATE_REJECTED";
        case LLR_STATE_REJECT_PENDING:   return "STATE_REJECT_PENDING";
        case LLR_STATE_REMOVED:          return "STATE_REMOVED";
        case LLR_STATE_REMOVE_PENDING:   return "STATE_REMOVE_PENDING";
        case LLR_STATE_RESUME_PENDING:   return "STATE_RESUME_PENDING";
        case LLR_STATE_RUNNING:          return "STATE_RUNNING";
        case LLR_STATE_STARTING:         return "STATE_STARTING";
        case LLR_STATE_SUBMISSION_ERR:   return "STATE_SUBMISSION_ERR";
        case LLR_STATE_TERMINATED:       return "STATE_TERMINATED";
        case LLR_STATE_UNEXPANDED:       return "STATE_UNEXPANDED";
        case LLR_STATE_VACATED:          return "STATE_VACATED";
        case LLR_STATE_VACATE_PENDING:   return "STATE_VACATE_PENDING";
        default:                         return "UNKNOWN_STATE";
        }
}

int one_job_task(llr_element_t *job)
{
    llr_element_t *err=NULL;
    int rc;
    char *jobid=NULL;
    llr_data_list_t step_list;
    void *step;
    llr_element_t *cred=NULL;
    pair<int,unsigned long> memtasks;

    rc=llr_get_data(rmh,job,LLR_JobGetStepList,&step_list,&err);
    if(rc!=LLR_API_OK)
    {
        if(err)
           llr_error(&err,LLR_ERROR_PRINT_STDOUT);
        return -1;
    }
    step=NULL;
    rc=llr_get_data(rmh,&step_list,LLR_JobGetFirstStep,&step,&err);
    while(step)
    {
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepID,&jobid,&err);
        string s=jobid;
        int p=s.find('@');
        if(p!=-1)
            s=s.substr(0,p);
        memtasks.first=figure_out_cores(job,step);
        memtasks.second=figure_out_memory(job,step);
        if(memtasks.first>300000)
        {
            memtasks.first=1;
        }
        steps.insert(make_pair(s.c_str(),memtasks));
        err=NULL;
        rc=llr_get_data(rmh,&step_list,LLR_JobGetNextStep,&step,&err);
    }

    return 0;
}



int one_job(llr_element_t *job)
{
    llr_element_t *err=NULL;
    int rc;
    char *jobid=NULL;
    llr_data_list_t step_list;
    void *step;
    llr_element_t *cred=NULL;

    rc=llr_get_data(rmh,job,LLR_JobGetStepList,&step_list,&err);
    if(rc!=LLR_API_OK)
    {
        if(err)
           llr_error(&err,LLR_ERROR_PRINT_STDOUT);
        return -1;
    }
    step=NULL;
    rc=llr_get_data(rmh,&step_list,LLR_JobGetFirstStep,&step,&err);
    while(step)
    {
        struct Job j;

        memset(&j,0,sizeof(struct Job));
        rc=llr_get_data(rmh,job,LLR_JobCredential,&cred,&err);
        err=NULL;
        rc=llr_get_data(rmh,cred,LLR_CredentialUserName,&jobid,&err);
        err=NULL;
        strcpy(j.user,jobid);
        rc=llr_get_data(rmh,step,LLR_StepID,&jobid,&err);
        err=NULL;
        strcpy(j.jobid,jobid);
        rc=llr_get_data(rmh,job,LLR_JobName,&jobid,&err);
        err=NULL;
        strcpy(j.jobname,jobid);
        rc=llr_get_data(rmh,job,LLR_JobSubmitTime,&j.submitTime,&err);
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepAccountNumber,&jobid,&err);
        err=NULL;
        strcpy(j.account,jobid);
        rc=llr_get_data(rmh,step,LLR_StepComment,&jobid,&err);
        err=NULL;
        strcpy(j.comment,jobid);
        rc=llr_get_data(rmh,step,LLR_StepLoadLevelerGroup,&jobid,&err);
        err=NULL;
        strcpy(j.group,jobid);
        rc=llr_get_data(rmh,step,LLR_StepJobClass,&jobid,&err);
        err=NULL;
        strcpy(j.jobClass,jobid);
        rc=llr_get_data(rmh,step,LLR_StepState,&j.status,&err);
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepCompletionCode,&j.app_status,&err);
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepParallelMode,&j.mode,&err);
        err=NULL;
        j.tasks=(j.mode==0?1:figure_out_cores(job,step));
        rc=llr_get_data(rmh,step,LLR_StepStartTime,&j.startTime,&err);
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepWallClockLimitHard,&j.wallclockRequested,&err);
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepWallClockUsed,&j.wallclockUsed,&err);
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepCompletionDate,&j.completeTime,&err);
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepHostList,&j.procs,&err);
        err=NULL;
        rc=llr_get_data(rmh,step,LLR_StepNodeCount,&j.nodes,&err);
        err=NULL;
        if(!j.startTime && j.completeTime)
              j.completeTime=0;
        //if(j.startTime)
        //   j.exec_time=step->usage_info.step_rusage.ru_utime.tv_sec+step->usage_info.step_rusage.ru_stime.tv_sec;
        j.mem=figure_out_memory(job,step);
        process_job(&j);
        err=NULL;
        rc=llr_get_data(rmh,&step_list,LLR_JobGetNextStep,&step,&err);
    }

    return 0;
}


int process_record( LL_job *job )
{
    LL_job_step *step;
    int num_cores,walltime,mem;
    int i,k;
    struct Job j;

    //memset(&j,0,sizeof(struct Job));
    //strcpy(j.user,job->owner);
    //strcpy(j.jobname,job->job_name);
    for( i=0; i<job->steps; i++ ) 
    {
        memset(&j,0,sizeof(struct Job));
        strcpy(j.user,job->owner);
        strcpy(j.jobname,job->job_name);
        step = job->step_list[i];
        sprintf(j.jobid,"%s.%d.%d",step->id.from_host, step->id.cluster, step->id.proc);

        j.tasks=step->cpus_requested;
        if(!j.tasks)
        {
            STEPS::iterator it=steps.find(j.jobid);
            if(it!=steps.end())
            {
                j.tasks=it->second.first;
                j.mem=it->second.second;
            }
            else
            {
                if(!j.tasks)
                {
                    j.tasks=step->max_processors;
                    if(!j.tasks)
                        j.tasks=step->num_processors;
                }
                j.mem=step->memory_requested;
            }
        }
        if(step->parallel_threads)
              j.tasks*=step->parallel_threads;
        j.mode=(j.tasks>1?1:0);
        strcpy(j.account,step->account_no);
        strcpy(j.group,step->group_name);
        strcpy(j.jobClass,step->stepclass);
        j.status=step->status;
        j.flags=step->flags;
        j.app_status=step->completion_code;
	j.completeTime=step->completion_date;
        j.wallclockRequested=step->limits.hard_wall_clock_limit;
        j.startTime=step->start_time;
        if(!j.startTime && j.completeTime)
              j.completeTime=0;
        j.submitTime=step->q_date;
        if(j.startTime)
           j.exec_time=step->usage_info.step_rusage.ru_utime.tv_sec+step->usage_info.step_rusage.ru_stime.tv_sec;
        strcpy(j.exec,step->cmd);
        strcpy(j.iwd,step->iwd);
        j.nodes=step->num_processors;
        j.procs=step->processor_list;
        if(!j.mem)
            j.mem=step->memory_requested;
        if(!j.mem)
            j.mem=step->memory_requested64;
        process_job(&j);
        //printf("Mem requested: %d\n",step->memory_requested);
        //printf("Mem requested64: %lu\n",step->memory_requested64);
        //printf("Mem used: %d\n",step->adapter_used_memory);
        //printf("Mem used64: %lu\n",step->usage_info64.step_rusage64.ru_idrss);
    }
    return 0;
}


int main(int argc, char *argv[])
{
    const char *ver=ll_version();
    int rc,i;
    llr_element_t *err=NULL;

    if(argc<2)
    {
        printf("Usage: %s <history file name> [history files]\n",argv[0]);
        return -1;
    }
    rc=llr_init_resmgr(LLR_API_VERSION,&rmh,&err);
    if(rc!=LLR_API_OK)
    {
        if(err)
           llr_error(&err,LLR_ERROR_PRINT_STDOUT);
       else
           fprintf(stderr,"Error initialising resource manager\n");
       return -1;
    } 
    for(i=1;i<argc;i++)
    {
        err=NULL;
#if USE_FULL_API
        rc=llr_get_history(rmh,argv[i],one_job,&err);
        if(rc!=LLR_API_OK)
        {
           fprintf(stderr,"Error getting history from %s\n",argv[i]);
           if(err)
               llr_error(&err,LLR_ERROR_PRINT_STDOUT);
       }
#else
       history_file=argv[i];
       fprintf(stderr,"Processing: %s\n",history_file);
       fprintf(stderr,"Phase 1\n");
       rc=llr_get_history(rmh,argv[i],one_job_task,&err);
       fprintf(stderr,"Phase 2\n");
       rc=GetHistory( argv[i], process_record, LL_JOB_VERSION );
       fprintf(stderr,"Done\n");
       steps.clear();
#endif
    } 
        
    llr_free_resmgr(&rmh,&err);
    return 0;
}

