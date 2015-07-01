#include <stdlib.h>
#include <string.h>
#include "slurm.h"
#include "job_resources.h"
#include "macros.h" // required for slurm_strtime

void load_and_print_machine_info(char * machine_name, job_info_msg_t *);
void print_node(node_info_t *, job_info_msg_t *);
void get_job_ids(int *, char *, char *, job_info_msg_t *);
int is_job_on_node(job_info_t *, char *);
int get_num_cores_of_job_on_node(job_info_t *, char *);

int main (int argc, char *argv[]) {

    int i, rc;
    job_info_msg_t * job_buffer_ptr = NULL;
    if (argc > 1) {
        printf("# <machine_name>|<total_mem_mb>|<avail_mem_mb>|<cpus>|<avail_cpus>|<job_ids>\n");
        slurm_conf_init(NULL);
        rc = slurm_load_jobs((time_t) NULL, &job_buffer_ptr, SHOW_DETAIL);
        if (rc) {
            slurm_perror ("slurm_load_jobs error");
            return;
        }
        for (i=1; i<argc; i++) {
            load_and_print_machine_info(argv[i], job_buffer_ptr);
        }
    }
    return 0;
}

void load_and_print_machine_info(char * machine_name, job_info_msg_t * job_buffer_ptr) {

    int i, rc;
    node_info_msg_t * node_buffer_ptr;
    node_info_t * node_ptr;

    rc = (int) slurm_load_node_single (&node_buffer_ptr, machine_name, 0);
    if (rc) {
        slurm_perror("slurm_load_node_single error");
    }
    for (i = 0, node_ptr = node_buffer_ptr->node_array; i < node_buffer_ptr->record_count; i++, node_ptr++) {
        print_node(node_ptr, job_buffer_ptr);
    }
}


void print_node (node_info_t * node_ptr, job_info_msg_t * job_buffer_ptr) {
   
    int alloc_cpus = 0;
    int avail_cpus = 0;
    int alloc_memory = 0;
    char free_memory_str[128], memory_str[128];
    slurm_get_select_nodeinfo(node_ptr->select_nodeinfo, SELECT_NODEDATA_SUBCNT, NODE_STATE_ALLOCATED, &alloc_cpus);
    slurm_get_select_nodeinfo(node_ptr->select_nodeinfo, SELECT_NODEDATA_MEM_ALLOC, NODE_STATE_ALLOCATED, &alloc_memory);
    if (alloc_memory > node_ptr->real_memory) {
      /* convert_num_unit apparently doesn't like negative values: a negative memory resulted in 4.00P (peta-bytes) */
      sprintf(free_memory_str, "%dM", (node_ptr->real_memory - alloc_memory));
    } else {
      convert_num_unit((node_ptr->real_memory - alloc_memory), free_memory_str, sizeof(free_memory_str), UNIT_MEGA);
    }
    convert_num_unit(node_ptr->real_memory, memory_str, sizeof(memory_str), UNIT_MEGA);
    // note that slurm counts cores of suspended jobs to alloc_cpus!!!!
    avail_cpus = node_ptr->cpus - alloc_cpus;
    char * job_id_string = malloc(sizeof(char) * 8192);
    job_id_string[0] = '\0';
    get_job_ids(&avail_cpus, job_id_string, node_ptr->name, job_buffer_ptr);
    printf("%s|%s|%s|%d|%d|%s\n", node_ptr->name, memory_str, free_memory_str, node_ptr->cpus, avail_cpus, job_id_string);
    free(job_id_string);
}

void get_job_ids(int * avail_cpus, char * job_id_string, char * node_name, job_info_msg_t * job_buffer_ptr) {

    int error_code = SLURM_SUCCESS, i;
    uint32_t array_id = NO_VAL;
    job_info_t *job_ptr = NULL;
    char *end_ptr = NULL;
    int count = 0;

    for (i = 0, job_ptr = job_buffer_ptr->job_array; i<job_buffer_ptr->record_count; i++, job_ptr++) {
        if ((array_id != NO_VAL) && (array_id != job_ptr->array_task_id))
            continue;
        if (is_job_on_node(job_ptr, node_name) > 0) {
            if (count > 0) {
                strcat(job_id_string, ",");
            }
            char tmp[20];
            sprintf(tmp, "%d", job_ptr->job_id);
            if (job_ptr->job_state == 2) { // suspended
                // add those cores back to avail_cpus
                *avail_cpus += get_num_cores_of_job_on_node(job_ptr, node_name);
            }
            strcat(job_id_string, tmp);
            count++;
        } 
    }
}

int is_job_on_node(job_info_t * job_ptr, char * node_name) {

    job_resources_t *jobres = job_ptr->job_resrcs;
    bitstr_t *core_bitmap;
    int i, j, bit_inx, bit_reps, sock_inx, rel_node_inx, last;
    int abs_node_inx = job_ptr->node_inx[i];
    char *host;
    hostlist_t hl, hl_last;

    if (!jobres) {
        return 0;
    }

    i = bit_inx = sock_inx = 0;
    hl = hostlist_create(jobres->nodes);
    for (rel_node_inx=0; rel_node_inx < jobres->nhosts; rel_node_inx++) {
        host = hostlist_shift(hl);
        if (strcmp(host, node_name) == 0) {
            return 1;
        }
    }
    return 0;
}

int get_num_cores_of_job_on_node(job_info_t * job_ptr, char * node) {

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
        return 0;
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
        if (strcmp(host, node) == 0) {
            return core_count;
        }
    }
    return 0;
}
