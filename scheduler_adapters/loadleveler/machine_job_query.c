static char machine__job_query_sccsid[] = "@(#) src/ll/samples/lldata_access/machine_job_query.c, ll.api, ll_rsur2, rsur21042a 1.5.2.2 4/16/10 15:12:24";
/*     
 * ---------------------------------------------------------------------
 * This sample program shows how LoadLeveler's Data Access API can be 
 * used to obtain machine, job, and cluster information. The program 
 * consists of three steps:
 *   1. Get information of selected machines in the LoadLeveler cluster.
 *   2. Get information of jobs of selected classes.
 *   3. Get floating consumable resource information of the LoadLeveler 
 *      cluster.
 *
 * Notes:
 *   1. The host_list of machine names must be modified to match your 
 *      configuration.
 *   2. The class_list of class names must be modified to match your 
 *      configuration.
 * ---------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "llapi.h"

main(int argc, char *argv[])
{
   LL_element *queryObject, *machine, *resource, *cluster;
   LL_element *job, *step, *node, *task, *credential, *resource_req, *mcluster;
   int rc, obj_count, err_code, value;
   int64_t value64;
   double load_avg;
   enum StepState step_state;
   SmtStateType_t smt_state;
   char **host_list, **class_list;
   char *name, *res_name, *step_id, *job_class, *node_req, *cluster_name;
   char *task_exec, *ex_args, *startd_state;

   /* Step 1: Display information of selected machines in the LL cluster */

   /* Initialize the query: Machine query */
   queryObject = ll_query(MACHINES);
   if (!queryObject) {
      printf("Query MACHINES: ll_query() returns NULL.\n"); exit(1);
   }

   /* Set query parameters: query specific machines by name */
   host_list = (char **)malloc(3*sizeof(char *));
   host_list[0] = "compute-a1-001-p";
   host_list[1] = "compute-a1-002-p";
   host_list[2] = NULL;
   rc = ll_set_request(queryObject, QUERY_HOST, host_list, ALL_DATA);
   if (rc) {
      printf("Query MACHINES: ll_set_request() return code is non-zero.\n"); exit(1);
   }

   /* Get the machine objects from the LoadL_negotiator (central manager) daemon */
   machine = ll_get_objs(queryObject, LL_CM, NULL, &obj_count, &err_code);
   if (machine == NULL) {
      printf("Query MACHINES: ll_get_objs() returns NULL. Error code = %d\n", err_code);
   }
   printf("Number of machines objects returned = %d\n", obj_count);

   /* Process the machine objects */
   while(machine) {
      rc = ll_get_data(machine, LL_MachineName, &name);
      if (!rc) {
         printf("Machine name: %s ------------------\n", name); free(name);
      }
      rc = ll_get_data(machine, LL_MachineStartdState, &startd_state);
      if (rc) {
         printf("Query MACHINES: ll_get_data() return code is non-zero.\n"); exit(1);
      }
      printf("Startd State: %s\n", startd_state);
      if (strcmp(startd_state, "Down") != 0) {
         rc = ll_get_data(machine, LL_MachineRealMemory64, &value64);
         if (!rc) printf("Total Real Memory: %lld MB\n", value64);
         rc = ll_get_data(machine, LL_MachineVirtualMemory64, &value64);
         if (!rc) printf("Free Swap Space: %lld KB\n", value64);
         rc = ll_get_data(machine, LL_MachineLoadAverage, &load_avg);
         if (!rc) printf("Load Average: %f\n", load_avg);
      }
      free(startd_state);

      rc = ll_get_data(machine, LL_MachineSMTState, &smt_state);
      if (!rc) {
         if (smt_state == SMT_ENABLED) {
            printf("SMT state: Enabled\n");
         } else if (smt_state == SMT_DISABLED) {
            printf("SMT state: Disabled\n");
         } else {
            printf("SMT state: Not support\n");
         }
      }

      /* Consumable Resources associated with this machine */
      resource = NULL;
      ll_get_data(machine, LL_MachineGetFirstResource, &resource);
      while(resource) {
         rc = ll_get_data(resource, LL_ResourceName, &res_name);
         if (!rc) {printf("Resource Name = %s\n", res_name); free(res_name);}
         rc = ll_get_data(resource, LL_ResourceInitialValue64, &value64);
         if (!rc) printf("   Total: %lld\n", value64);
         rc = ll_get_data(resource, LL_ResourceAvailableValue64, &value64);
         if (!rc) printf("   Available: %lld\n", value64);
         resource = NULL;
         ll_get_data(machine, LL_MachineGetNextResource, &resource);
      }
      machine = ll_next_obj(queryObject);
   }

   /* Free objects obtained from Negotiator */
   ll_free_objs(queryObject);
   /* Free query element */
   ll_deallocate(queryObject);

   /* Step 2: Display information of selected jobs */

   /* Initialize the query: Job query  */
   printf("==================================================================\n");
   queryObject = ll_query(JOBS);
   if (!queryObject) {
      printf("Query JOBS: ll_query() returns NULL.\n");
      exit(1);
   }

   /* Query all jobs of class "Parallel", "small", and "No_Class" submitted to c209f1n01, c209f1n05 */
   class_list = (char **)malloc(4*sizeof(char *));
   class_list[0] = "Parallel";
   class_list[1] = "No_Class";
   class_list[2] = "small";
   class_list[3] = NULL;
   rc = ll_set_request(queryObject, QUERY_HOST, host_list, ALL_DATA);
   if (rc) {printf("Query JOBS: ll_set_request() return code is non-zero.\n"); exit(1);}
   rc = ll_set_request(queryObject, QUERY_CLASS, class_list, ALL_DATA);
   if (rc) {printf("Query JOBS: ll_set_request() return code is non-zero.\n"); exit(1);}

   /* Get the requested job objects from the Central Manager */
   job = ll_get_objs(queryObject, LL_CM, NULL, &obj_count, &err_code);
   if (job == NULL) {
      printf("Query JOBS: ll_get_objs() returns NULL. Error code = %d\n", err_code);
   }
   printf("Number of job objects returned = %d\n", obj_count);

   /*  Process the job objects and display selected information of each job step.
    *
    *  Notes:
    *    1. Since LL_element is defined as "void" in llapi.h, when using
    *       ll_get_data it is important that a valid "specification" parameter
    *       be used for a given "element" argument.
    *    2. Checking of return code is not always made in the following loop to
    *       minimize the length of the listing.
    */

   while(job) {
      printf("------------------------------------------------------------------\n");
      rc = ll_get_data(job, LL_JobName, &name);
      if (!rc) {printf("Job name: %s\n", name); free(name);}

      rc = ll_get_data(job, LL_JobCredential, &credential);
      if (!rc) {
         rc = ll_get_data(credential, LL_CredentialUserName, &name);
         if (!rc) {printf("Job owner: %s\n", name); free(name);}
         rc = ll_get_data(credential, LL_CredentialGroupName, &name);
         if (!rc) {printf("Unix Group: %s\n", name); free(name);}
      }
      step = NULL;
      ll_get_data(job, LL_JobGetFirstStep, &step);
      while(step) {
         printf("  ----------------------------------------------------------------\n");
         rc = ll_get_data(step, LL_StepID, &step_id);
         if (!rc) {printf("  Step ID: %s\n", step_id); free(step_id);}
         rc = ll_get_data(step, LL_StepJobClass, &job_class);
         if (!rc) {printf("  Step Job Class: %s\n", job_class); free(job_class);}
         rc = ll_get_data(step, LL_StepCpuStepLimitHard64, &value64);
         if (!rc) {printf("  Job Step CPU Hard Limit: %lld\n", value64);}
         rc = ll_get_data(step, LL_StepCpuLimitHard64, &value64);
         if (!rc) {printf("  Step CPU Hard Limit: %lld\n", value64);}
         rc = ll_get_data(step, LL_StepFileLimitHard64, &value64);
         if (!rc) {printf("  Step File Hard Limit: %lld\n", value64);}
         rc = ll_get_data(step, LL_StepState, &step_state);
         if (!rc) {
            if (step_state == STATE_RUNNING) {
               printf("  Step Status: Running\n");
               printf("  Allocated Hosts:\n");
               machine = NULL;
               ll_get_data(step, LL_StepGetFirstMachine, &machine);
               while(machine) {
                  rc = ll_get_data(machine, LL_MachineName, &name);
                  if (!rc) { printf("    %s\n", name); free(name); }
                  machine = NULL;
                  ll_get_data(step, LL_StepGetNextMachine, &machine);
               }
            }
            else {
               printf("  Step Status: Not Running\n");
            }
         }

         rc = ll_get_data(step, LL_StepScaleAcrossClusterCount, &value);
         if (!rc) printf("LL_StepScaleAcrossClusterCount: %d\n", value); 
         mcluster = NULL;
         ll_get_data(step, LL_StepGetFirstScaleAcrossCluster, &mcluster);
         while (mcluster) {
            rc = ll_get_data(mcluster, LL_MClusterName, &cluster_name);
            if (!rc) {printf("Cluster Name: %s\n", cluster_name); free(cluster_name);}

            mcluster = NULL;
            ll_get_data(step, LL_StepGetNextScaleAcrossCluster, &mcluster);
         }
	 
         node = NULL;
         ll_get_data(step, LL_StepGetFirstNode, &node);
         while(node) {
            rc = ll_get_data(node, LL_NodeRequirements, &node_req);
            if (!rc) {printf("    Node Requirements: %s\n", node_req); free(node_req);}
            task = NULL;
            ll_get_data(node, LL_NodeGetFirstTask, &task);
            while(task) {
               rc = ll_get_data(task, LL_TaskExecutable, &task_exec);
               if (!rc) {printf("      Task Executable: %s\n", task_exec); free(task_exec);}
               rc = ll_get_data(task, LL_TaskExecutableArguments, &ex_args);
               if (!rc) {printf("      Task Executable Arguments: %s\n",ex_args); free(ex_args);}
               resource_req = NULL;
               ll_get_data(task, LL_TaskGetFirstResourceRequirement, &resource_req);
               while(resource_req) {
                  rc = ll_get_data(resource_req, LL_ResourceRequirementName, &name);
                  if (!rc) {printf("        Resource Req Name: %s\n", name); free(name);}
                  rc = ll_get_data(resource_req, LL_ResourceRequirementValue64, &value64);
                  if (!rc) {printf("        Resource Req Value: %lld\n", value64);}
                  resource_req = NULL;
                  ll_get_data(task, LL_TaskGetNextResourceRequirement, &resource_req);
               }
               task = NULL;
               ll_get_data(node, LL_NodeGetNextTask, &task);
            }
            node = NULL;
            ll_get_data(step, LL_StepGetNextNode, &node);
         }
         step = NULL;
         ll_get_data(job, LL_JobGetNextStep, &step);
      }
      job = ll_next_obj(queryObject);
   }
   ll_free_objs(queryObject);
   ll_deallocate(queryObject);

   /* Step 3: Display Floating Consumable Resources information of LL cluster. */

   /* Initialize the query: Cluster query  */
   printf("==================================================================\n");
   queryObject = ll_query(CLUSTERS);
   if (!queryObject) {
      printf("Query CLUSTERS: ll_query() returns NULL.\n");
      exit(1);
   }
   ll_set_request(queryObject, QUERY_ALL, NULL, ALL_DATA);
   cluster = ll_get_objs(queryObject, LL_CM, NULL, &obj_count, &err_code);
   if (!cluster) {
      printf("Query CLUSTERS: ll_get_objs() returns NULL. Error code = %d\n", err_code);
   }
   printf("Number of Cluster objects = %d\n", obj_count);
   while(cluster) {
      resource = NULL;
      ll_get_data(cluster, LL_ClusterGetFirstResource, &resource);
      while(resource) {
         rc = ll_get_data(resource, LL_ResourceName, &res_name);
         if (!rc) {printf("Resource Name = %s\n", res_name); free(res_name);}
         rc = ll_get_data(resource, LL_ResourceInitialValue64, &value64);
         if (!rc) {printf("Resource Initial Value = %lld\n", value64);}
         rc = ll_get_data(resource, LL_ResourceAvailableValue64, &value64);
         if (!rc) {printf("Resource Available Value = %lld\n", value64);}
         resource = NULL;
         ll_get_data(cluster, LL_ClusterGetNextResource, &resource);
      }
      cluster = ll_next_obj(queryObject);
   }
   ll_free_objs(queryObject);
   ll_deallocate(queryObject);
}

