#include <stdlib.h>
#include <string.h>
#include "slurm.h"
#include "job_resources.h"
#include "macros.h" // required for slurm_strtime
#include "slurm_protocol_defs.h"

job_info_msg_t *old_job_info_ptr = NULL;

void load_and_print_job(uint32_t);
void print_job(job_info_t * job_ptr);
int load_job(job_info_msg_t ** job_buffer_pptr, uint32_t job_id);
void _sprint_range(char *str, uint32_t str_size, uint32_t lower, uint32_t upper);
void make_time_str (time_t *time, char *string, int size);
void get_runtime(job_info_t *, char *);
void get_walltime(job_info_t *, char *);
void print_jobresources(job_info_t * job_ptr);
void get_memory(job_info_t *, char *);

int main (int argc, char *argv[]) {

    int i;
    char * tmp;
    uint32_t jobid = 0;
    if (argc > 1) {
        printf("# jobid|username|jobstatus|queue|req_num_cores|req_mem|job_directory|submit_time|start_time|req_walltime|runtime|comma-sep list of nodes [node:cpucores:mem]\n");
        slurm_conf_init(NULL);
        for (i=1; i<argc; i++) { 
            jobid = (uint32_t) strtol(argv[i], &tmp, 10);
            load_and_print_job(jobid);
        }
    }
    return 0;
}

/*
 * Load all jobs and print information about each job
 */
void load_and_print_job (uint32_t jobid) {

    int error_code = SLURM_SUCCESS, i;
    uint32_t array_id = NO_VAL;
    job_info_msg_t * job_buffer_ptr = NULL;
    job_info_t *job_ptr = NULL;
    char *end_ptr = NULL;

    error_code = (int) load_job(&job_buffer_ptr, jobid);
    if (error_code) {
        slurm_perror ("slurm_load_jobs error");
        return;
    }

    for (i = 0, job_ptr = job_buffer_ptr->job_array; i < job_buffer_ptr->record_count; i++, job_ptr++) {
        if ((array_id != NO_VAL) && (array_id != job_ptr->array_task_id)) {
            continue;
        }
        print_job(job_ptr);
    }
}

/*
 * Print information about a job to stdout
 */
void print_job (job_info_t * job_ptr) {

    char * user_name = uid_to_string((uid_t)job_ptr->user_id);
    uint32_t job_id = job_ptr->job_id;
    char * job_state = job_state_string(job_ptr->job_state);
    char * partition = job_ptr->partition;
    char * batch_host = (job_ptr->batch_host == NULL) ? "N/A" : job_ptr->batch_host;
    char req_cores[128];
    char submit_time_str[32];
    char start_time_str[32];
    char runtime[128];
    char walltime[128];
    char mem[128];

    _sprint_range(req_cores, sizeof(req_cores), job_ptr->num_cpus, job_ptr->max_cpus);
    make_time_str((time_t *)&job_ptr->submit_time, submit_time_str, sizeof(submit_time_str));
    make_time_str((time_t *)&job_ptr->start_time, start_time_str, sizeof(start_time_str));
    char * work_dir = job_ptr->work_dir;
    get_runtime(job_ptr, runtime);
    get_walltime(job_ptr, walltime);
    get_memory(job_ptr, mem);
    printf("%u|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|", job_id, user_name, job_state, partition, req_cores, mem, work_dir, submit_time_str, start_time_str, walltime, runtime);
    print_jobresources(job_ptr);
    printf("\n");
}

/*
 * Load job information
 */
int load_job(job_info_msg_t ** job_buffer_pptr, uint32_t jobid) {

    int error_code;
    job_info_msg_t * job_info_ptr = NULL;
    error_code = slurm_load_job(&job_info_ptr, jobid, SHOW_DETAIL);
    if (error_code == SLURM_SUCCESS) {
        *job_buffer_pptr = job_info_ptr;
    }
    return error_code;
}

/*
 * Borrowed and modified from src/api/job_info.c
 */
void _sprint_range(char *str, uint32_t str_size, uint32_t lower, uint32_t upper) {

    char tmp[128];
    uint32_t cluster_flags = slurmdb_setup_cluster_flags();

    snprintf(tmp, sizeof(tmp), "%u", lower);
    if (upper > 0) {
        char tmp2[128];
        snprintf(tmp2, sizeof(tmp2), "%u", upper);
        snprintf(str, str_size, "%s-%s", tmp, tmp2);
    } else {
        snprintf(str, str_size, "%s", tmp);
    }
}

/*
 * Create a human readable time string
 */
void make_time_str (time_t *time, char *string, int size) {

    struct tm time_tm;
    localtime_r(time, &time_tm);
    if ((*time == (time_t) 0) || (*time == (time_t) INFINITE)) {
        snprintf(string, size, "Unknown");
    } else {
        static const char *display_fmt = "%F %T";
        slurm_strftime(string, size, display_fmt, &time_tm);
    }
}

void get_runtime(job_info_t * job_ptr, char * runtime) {

    time_t tmp;
    if (IS_JOB_PENDING(job_ptr)) {
        tmp = 0;
    } else if (IS_JOB_SUSPENDED(job_ptr)) {
        tmp = job_ptr->pre_sus_time;
    } else {
        time_t end_time;
        if (IS_JOB_RUNNING(job_ptr) || (job_ptr->end_time == 0)) {
            end_time = time(NULL);
        } else {
            end_time = job_ptr->end_time;
        }
        if (job_ptr->suspend_time) {
            tmp = (time_t) (difftime(end_time, job_ptr->suspend_time) + job_ptr->pre_sus_time);
        } else {
            tmp = (time_t) difftime(end_time, job_ptr->start_time);
        }
    }
    secs2time_str(tmp, runtime, 128);
}

void get_walltime(job_info_t * job_ptr, char * walltime) {

    if (job_ptr->time_limit == NO_VAL)
        sprintf(walltime, "N/A");
    else {
        mins2time_str(job_ptr->time_limit, walltime, 128);
    }
}

void get_memory(job_info_t * job_ptr, char * mem_str) {

    char tmp[128];
    if (job_ptr->pn_min_memory & MEM_PER_CPU) {
        job_ptr->pn_min_memory &= (~MEM_PER_CPU);
        convert_num_unit((float)job_ptr->pn_min_memory, tmp, sizeof(tmp), UNIT_MEGA);
        sprintf(mem_str, "%s (per task)", tmp); 
    } else {
        convert_num_unit((float)job_ptr->pn_min_memory, tmp, sizeof(tmp), UNIT_MEGA);
        sprintf(mem_str, "%s (per node)", tmp);
    }
}

void print_jobresources(job_info_t * job_ptr) {

    job_resources_t *jobres = job_ptr->job_resrcs;
    bitstr_t *core_bitmap;
    int i, j, bit_inx, bit_reps, sock_inx, sock_reps, rel_node_inx, last;
    int abs_node_inx = job_ptr->node_inx[i];
    char *host;
    char *out = NULL;
    uint32_t *last_mem_alloc_ptr = NULL;
    uint32_t last_mem_alloc = NO_VAL;
    uint32_t core_count;
    char *last_hosts;
    char tmp[32];
    hostlist_t hl, hl_last;

    if (!jobres) {
        printf("N/A");
        return;
    }

    i = bit_inx = sock_inx = sock_reps = 0;
    hl = hostlist_create(jobres->nodes);
    for (rel_node_inx=0; rel_node_inx < jobres->nhosts; rel_node_inx++) {
        core_count = 0;
        if (sock_reps >= jobres->sock_core_rep_count[sock_inx]) {
            sock_inx++;
            sock_reps = 0;
        }
        sock_reps++;

        bit_reps = jobres->sockets_per_node[sock_inx] * jobres->cores_per_socket[sock_inx];
        core_bitmap = bit_alloc(bit_reps);
        for (j=0; j < bit_reps; j++) {
            if (bit_test(jobres->core_bitmap, bit_inx)) {
                core_count++;
            }
            bit_inx++;
        }

        host = hostlist_shift(hl);
        convert_num_unit(jobres->memory_allocated[rel_node_inx], tmp, sizeof(tmp), UNIT_MEGA);
        printf("%s:%d:%s", host, core_count, tmp);
        if (rel_node_inx < jobres->nhosts-1) {
            printf(",");
        }
    }     
}
