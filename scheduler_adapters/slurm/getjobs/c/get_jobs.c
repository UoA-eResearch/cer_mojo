#include <stdlib.h>
#include <string.h>
#include "slurm.h"
#include "macros.h" // required for slurm_strtime

job_info_msg_t *old_job_info_ptr = NULL;

void load_and_print_jobs();
void print_job(job_info_t * job_ptr, char * user);
int load_job(job_info_msg_t ** job_buffer_pptr, uint32_t job_id);
void _sprint_range(char *str, uint32_t str_size, uint32_t lower, uint32_t upper);
void make_time_str (time_t *time, char *string, int size);

int main (int argc, char *argv[]) {

    char * user = NULL;
    if (argc == 2) {
        user = argv[1];
    }

    slurm_conf_init(NULL);
    load_and_print_jobs(user);
    return 0;
}

/*
 * Load all jobs and print information about each job
 */
void load_and_print_jobs (char * user) {

    int error_code = SLURM_SUCCESS, i;
    uint32_t array_id = NO_VAL;
    job_info_msg_t * job_buffer_ptr = NULL;
    job_info_t *job_ptr = NULL;
    char *end_ptr = NULL;

    error_code = (int) load_job(&job_buffer_ptr, 0);
    if (error_code) {
        slurm_perror ("slurm_load_jobs error");
        return;
    }

    printf("# jobid|jobstate|username|queue|requestedcores|mainnode|submittime|starttime\n");
    for (i = 0, job_ptr = job_buffer_ptr->job_array; i < job_buffer_ptr->record_count; i++, job_ptr++) {
        if ((array_id != NO_VAL) && (array_id != job_ptr->array_task_id)) {
            continue;
        }
        print_job(job_ptr, user);
    }
}

/*
 * Print information about a job to stdout
 */
void print_job (job_info_t * job_ptr, char * user) {

    char * user_name = uid_to_string((uid_t)job_ptr->user_id);
    if (user == NULL || strcmp(user, user_name) == 0) {
        uint32_t job_id = job_ptr->job_id;
        char * job_state = job_state_string_compact(job_ptr->job_state);
        char * partition = job_ptr->partition;
        char * batch_host = (job_ptr->batch_host == NULL) ? "N/A" : job_ptr->batch_host;
        char req_cores[128];
        char submit_time_str[32];
        char start_time_str[32];
        _sprint_range(req_cores, sizeof(req_cores), job_ptr->num_cpus, job_ptr->max_cpus);
        make_time_str((time_t *)&job_ptr->submit_time, submit_time_str, sizeof(submit_time_str));
        make_time_str((time_t *)&job_ptr->start_time, start_time_str, sizeof(start_time_str));
        printf("%u|%s|%s|%s|%s|%s|%s|%s\n", job_id, job_state, user_name, partition, req_cores, batch_host, submit_time_str, start_time_str);
    }
}

/*
 * Load job information
 */
int load_job(job_info_msg_t ** job_buffer_pptr, uint32_t job_id) {

    int error_code;
    uint16_t show_flags = 0;
    job_info_msg_t * job_info_ptr = NULL;
    error_code = slurm_load_jobs((time_t) NULL, &job_info_ptr, show_flags);
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
