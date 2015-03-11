extern char * slurm_sprint_job_info ( job_info_t * job_ptr, int one_liner )
{
	int i, j;
	char time_str[32], *group_name, *user_name;
	char tmp1[128], tmp2[128], tmp3[128], tmp4[128], tmp5[128], tmp6[128];
...
	/****** Line 15 ******/
	if (cluster_flags & CLUSTER_FLAG_BG) {
		select_g_select_jobinfo_get(job_ptr->select_jobinfo,
					    SELECT_JOBDATA_NODE_CNT,
					    &min_nodes);
		if ((min_nodes == 0) || (min_nodes == NO_VAL)) {
			min_nodes = job_ptr->num_nodes;
			max_nodes = job_ptr->max_nodes;
		} else if (job_ptr->max_nodes)
			max_nodes = min_nodes;
	} else if (IS_JOB_PENDING(job_ptr)) {
		min_nodes = job_ptr->num_nodes;
		if ((min_nodes == 1) && (job_ptr->num_cpus > 1)
		    && job_ptr->ntasks_per_node
		    && (job_ptr->ntasks_per_node != (uint16_t) NO_VAL)) {
			int node_cnt2 = job_ptr->num_cpus;
			node_cnt2 = (node_cnt2 + job_ptr->ntasks_per_node - 1)
				    / job_ptr->ntasks_per_node;
			if (min_nodes < node_cnt2)
				min_nodes = node_cnt2;
		}
		max_nodes = job_ptr->max_nodes;
		if (max_nodes && (max_nodes < min_nodes))
			min_nodes = max_nodes;
	} else {
		min_nodes = job_ptr->num_nodes;
		max_nodes = 0;
	}

	_sprint_range(tmp1, sizeof(tmp1), job_ptr->num_cpus, job_ptr->max_cpus);
	_sprint_range(tmp2, sizeof(tmp2), min_nodes, max_nodes);
	if (job_ptr->boards_per_node == (uint16_t) NO_VAL)
		strcpy(tmp3, "*");
	else
		snprintf(tmp3, sizeof(tmp3), "%u", job_ptr->boards_per_node);
	if (job_ptr->sockets_per_board == (uint16_t) NO_VAL)
		strcpy(tmp4, "*");
	else
		snprintf(tmp4, sizeof(tmp4), "%u", job_ptr->sockets_per_board);
	if (job_ptr->cores_per_socket == (uint16_t) NO_VAL)
		strcpy(tmp5, "*");
	else
		snprintf(tmp5, sizeof(tmp5), "%u", job_ptr->cores_per_socket);
	if (job_ptr->threads_per_core == (uint16_t) NO_VAL)
		strcpy(tmp6, "*");
	else
		snprintf(tmp6, sizeof(tmp6), "%u", job_ptr->threads_per_core);
	snprintf(tmp_line, sizeof(tmp_line),
		 "NumNodes=%s NumCPUs=%s CPUs/Task=%u ReqB:S:C:T=%s:%s:%s:%s",
		 tmp2, tmp1, job_ptr->cpus_per_task, tmp3, tmp4, tmp5, tmp6);
	xstrcat(out, tmp_line);
	if (one_liner)
		xstrcat(out, " ");
	else
		xstrcat(out, "\n   ");

	/****** Line 16 MARTIN ******/
	if (job_ptr->sockets_per_node == (uint16_t) NO_VAL)
		strcpy(tmp1, "*");
	else
		snprintf(tmp1, sizeof(tmp1), "%u", job_ptr->sockets_per_node);
	if (job_ptr->ntasks_per_node == (uint16_t) NO_VAL)
		strcpy(tmp2, "*");
	else
		snprintf(tmp2, sizeof(tmp2), "%u", job_ptr->ntasks_per_node);
	if (job_ptr->ntasks_per_board == (uint16_t) NO_VAL)
		strcpy(tmp3, "*");
	else
		snprintf(tmp3, sizeof(tmp3), "%u", job_ptr->ntasks_per_board);
	if ((job_ptr->ntasks_per_socket == (uint16_t) NO_VAL) ||
	    (job_ptr->ntasks_per_socket == (uint16_t) INFINITE))
		strcpy(tmp4, "*");
	else
		snprintf(tmp4, sizeof(tmp4), "%u", job_ptr->ntasks_per_socket);
	if ((job_ptr->ntasks_per_core == (uint16_t) NO_VAL) ||
	    (job_ptr->ntasks_per_core == (uint16_t) INFINITE))
		strcpy(tmp5, "*");
	else
		snprintf(tmp5, sizeof(tmp5), "%u", job_ptr->ntasks_per_core);
	snprintf(tmp_line, sizeof(tmp_line),
		 "Socks/Node=%s NtasksPerN:B:S:C=%s:%s:%s:%s CoreSpec=%u",
		 tmp1, tmp2, tmp3, tmp4, tmp5, job_ptr->core_spec);
	xstrcat(out, tmp_line);
	if (one_liner)
		xstrcat(out, " ");
	else
		xstrcat(out, "\n   ");

	if (!job_resrcs)
		goto line15;

	if (cluster_flags & CLUSTER_FLAG_BG) {
		if ((job_resrcs->cpu_array_cnt > 0) &&
		    (job_resrcs->cpu_array_value) &&
		    (job_resrcs->cpu_array_reps)) {
			int length = 0;
			xstrcat(out, "CPUs=");
			length += 10;
			for (i = 0; i < job_resrcs->cpu_array_cnt; i++) {
				if (length > 70) {
					/* skip to last CPU group entry */
					if (i < job_resrcs->cpu_array_cnt - 1) {
						continue;
					}
					/* add ellipsis before last entry */
					xstrcat(out, "...,");
					length += 4;
				}

				snprintf(tmp_line, sizeof(tmp_line), "%d",
					 job_resrcs->cpus[i]);
				xstrcat(out, tmp_line);
				length += strlen(tmp_line);
				if (job_resrcs->cpu_array_reps[i] > 1) {
					snprintf(tmp_line, sizeof(tmp_line),
						 "*%d",
						 job_resrcs->cpu_array_reps[i]);
					xstrcat(out, tmp_line);
					length += strlen(tmp_line);
				}
				if (i < job_resrcs->cpu_array_cnt - 1) {
					xstrcat(out, ",");
					length++;
				}
			}
			if (one_liner)
				xstrcat(out, " ");
			else
				xstrcat(out, "\n   ");
		}
	} else {
		if (!job_resrcs->core_bitmap)
			goto line15;

		last  = bit_fls(job_resrcs->core_bitmap);
		if (last == -1)
			goto line15;

		hl = hostlist_create(job_resrcs->nodes);
		if (!hl) {
			error("slurm_sprint_job_info: hostlist_create: %s",
			      job_resrcs->nodes);
			return NULL;
		}
		hl_last = hostlist_create(NULL);
		if (!hl_last) {
			error("slurm_sprint_job_info: hostlist_create: NULL");
			hostlist_destroy(hl);
			return NULL;
		}

		bit_inx = 0;
		i = sock_inx = sock_reps = 0;
		abs_node_inx = job_ptr->node_inx[i];

/*	tmp1[] stores the current cpu(s) allocated	*/
		tmp2[0] = '\0';	/* stores last cpu(s) allocated */
		for (rel_node_inx=0; rel_node_inx < job_resrcs->nhosts;
		     rel_node_inx++) {

			if (sock_reps >=
			    job_resrcs->sock_core_rep_count[sock_inx]) {
				sock_inx++;
				sock_reps = 0;
			}
			sock_reps++;

			bit_reps = job_resrcs->sockets_per_node[sock_inx] *
				job_resrcs->cores_per_socket[sock_inx];

			core_bitmap = bit_alloc(bit_reps);
			for (j=0; j < bit_reps; j++) {
				if (bit_test(job_resrcs->core_bitmap, bit_inx))
					bit_set(core_bitmap, j);
				bit_inx++;
			}

			bit_fmt(tmp1, sizeof(tmp1), core_bitmap);
			FREE_NULL_BITMAP(core_bitmap);
			host = hostlist_shift(hl);
/*
 *		If the allocation values for this host are not the same as the
 *		last host, print the report of the last group of hosts that had
 *		identical allocation values.
 */
			if (strcmp(tmp1, tmp2) ||
			    (last_mem_alloc_ptr != job_resrcs->memory_allocated) || (job_resrcs->memory_allocated && (last_mem_alloc != job_resrcs->memory_allocated[rel_node_inx]))) {
				if (hostlist_count(hl_last)) {
					last_hosts = hostlist_ranged_string_xmalloc(hl_last);
					snprintf(tmp_line, sizeof(tmp_line),
						 "  Nodes=%s CPU_IDs=%s Mem=%u",
						 last_hosts, tmp2,
						 last_mem_alloc_ptr ?
						 last_mem_alloc : 0);
					xfree(last_hosts);
					xstrcat(out, tmp_line);
					if (one_liner)
						xstrcat(out, " ");
					else
						xstrcat(out, "\n   ");

					hostlist_destroy(hl_last);
					hl_last = hostlist_create(NULL);
				}
				strcpy(tmp2, tmp1);
				last_mem_alloc_ptr = job_resrcs->memory_allocated;
				if (last_mem_alloc_ptr)
					last_mem_alloc = job_resrcs-> memory_allocated[rel_node_inx];
				else
					last_mem_alloc = NO_VAL;
			}
			hostlist_push_host(hl_last, host);
			free(host);

			if (bit_inx > last)
				break;

			if (abs_node_inx > job_ptr->node_inx[i+1]) {
				i += 2;
				abs_node_inx = job_ptr->node_inx[i];
			} else {
				abs_node_inx++;
			}
		}

		if (hostlist_count(hl_last)) {
			last_hosts = hostlist_ranged_string_xmalloc(hl_last);
			snprintf(tmp_line, sizeof(tmp_line),
				 "  Nodes=%s CPU_IDs=%s Mem=%u",
				 last_hosts, tmp2,
				 last_mem_alloc_ptr ? last_mem_alloc : 0);
			xfree(last_hosts);
			xstrcat(out, tmp_line);
			if (one_liner)
				xstrcat(out, " ");
			else
				xstrcat(out, "\n   ");
		}
		hostlist_destroy(hl);
		hostlist_destroy(hl_last);
	}
	/****** Line 17 ******/
line15:
	if (job_ptr->pn_min_memory & MEM_PER_CPU) {
		job_ptr->pn_min_memory &= (~MEM_PER_CPU);
		tmp6_ptr = "CPU";
	} else
		tmp6_ptr = "Node";

	if (cluster_flags & CLUSTER_FLAG_BG) {
		convert_num_unit((float)job_ptr->pn_min_cpus,
				 tmp1, sizeof(tmp1), UNIT_NONE);
		snprintf(tmp_line, sizeof(tmp_line), "MinCPUsNode=%s",	tmp1);
	} else {
		snprintf(tmp_line, sizeof(tmp_line), "MinCPUsNode=%u",
			 job_ptr->pn_min_cpus);
	}

	xstrcat(out, tmp_line);
	convert_num_unit((float)job_ptr->pn_min_memory, tmp1, sizeof(tmp1),
			 UNIT_MEGA);
	convert_num_unit((float)job_ptr->pn_min_tmp_disk, tmp2, sizeof(tmp2),
			 UNIT_MEGA);
	snprintf(tmp_line, sizeof(tmp_line),
		 " MinMemory%s=%s MinTmpDiskNode=%s",
		 tmp6_ptr, tmp1, tmp2);
	xstrcat(out, tmp_line);
	if (one_liner)
		xstrcat(out, " ");
	else
		xstrcat(out, "\n   ");

}

