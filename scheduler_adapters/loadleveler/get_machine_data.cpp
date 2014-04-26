#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <map>
#include <string>
#include <iostream>
#include <sstream>
#include "llapi.h"

using namespace std;

struct Values
{
    Values():initial(0),available(0) {}
    int64_t initial;
    int64_t available;
};

typedef std::map<std::string,Values> VALUELIST;

int main(int argc, char *argv[])
{
   LL_element *queryObject, *machine, *resource, *cluster;
   int rc, obj_count, err_code, value, cpus;
   int64_t value64;
   enum StepState step_state;
   char **host_list, **class_list;
   char *name, *res_name, *step_id, *job_class, *node_req, *cluster_name;
   char *task_exec, *ex_args, *startd_state;
   int i;
   VALUELIST vl;
   Values v;

   if(argc<2)
   {
       cout << "Usage: " << argv[0] << " <machine name> [machine_name machine_name ...]" << endl;
       cout << "Output format: <machine name>|<real mem>|<free real mem>|<#cpus>|<#free cpus>|<consumable mem>|<free consumable mem>|<consumable vmem>|<free consumable vmem>" << endl;
       return -1;
   }

   /* Initialize the query: Machine query */
   queryObject = ll_query(MACHINES);
   if(!queryObject) 
   {
       cout << "Query MACHINES: ll_query() returns NULL." << endl; 
       return -1;
   }

   /* Set query parameters: query specific machines by name */
   host_list = (char **)malloc((argc+1)*sizeof(char *));
   for(i=0;i<argc;i++)
   {
       host_list[i] = argv[i+1];
   }
   host_list[i] = NULL;

   rc=ll_set_request(queryObject, QUERY_HOST, host_list, ALL_DATA);
   if(rc) 
   {
      cout << "Query MACHINES: ll_set_request() return code is non-zero." << endl;
      return -1;
   }

   /* Get the machine objects from the LoadL_negotiator (central manager) daemon */
   machine = ll_get_objs(queryObject, LL_CM, NULL, &obj_count, &err_code);
   /* Process the machine objects */
   // output: machine name|real mem mb|free mem mb|CPUs|used CPUs|ConsumableMemory|ConsumableMemory avail|ConsumableVirtualMemory|ConsumableVirtualMemory avail
   while(machine) 
   {
      rc = ll_get_data(machine, LL_MachineName, &name);
      if(rc) 
         continue;
      cout << name;
      free(name);
      rc = ll_get_data(machine, LL_MachineStartdState, &startd_state);
      if(rc)
         continue;
      //if(strcmp(startd_state, "Down")) 
      //{
         value64=0;
         rc = ll_get_data(machine, LL_MachineRealMemory64, &value64);
         cout << "|" << value64;
         value64=0;
         rc = ll_get_data(machine, LL_MachineFreeRealMemory64, &value64);
         cout << "|" << value64;
         cpus=0;
         rc = ll_get_data(machine, LL_MachineCPUs, &cpus);
         cout << "|" << cpus;
         value=0;
         rc = ll_get_data(machine, LL_MachineUsedCPUs, &value);
         cout << "|" << cpus-value;
      //}
      free(startd_state);

      /* Consumable Resources associated with this machine */
      vl.clear();
      resource = NULL;
      ll_get_data(machine, LL_MachineGetFirstResource, &resource);
      while(resource) 
      {
         rc = ll_get_data(resource, LL_ResourceName, &res_name);
         rc = ll_get_data(resource, LL_ResourceInitialValue64, &v.initial);
         rc = ll_get_data(resource, LL_ResourceAvailableValue64, &v.available);
         vl.insert(make_pair(res_name,v));
         free(res_name);
         resource = NULL;
         ll_get_data(machine, LL_MachineGetNextResource, &resource);
      }
//      v=vl["ConsumableCpus"];
//      printf("|%lld|%lld",v.initial,v.available);
      v=vl["ConsumableMemory"];
      cout << "|" << v.initial << "|" << v.available;
      v=vl["ConsumableVirtualMemory"];
      cout << "|" << v.initial << "|" << v.available << "|";

      char ** ppcBuffer;
      char ** ppChar;
      stringstream tmpstream;
      rc = ll_get_data(machine,LL_MachineStepList,&ppcBuffer);
      if((ppcBuffer!=NULL)&&(ppcBuffer[0]!=NULL)) { 
        for(ppChar = ppcBuffer; *ppChar!=NULL; ppChar++) { 
          tmpstream << *ppChar << ","; 
          free(*ppChar);
        } 
      }
      string tmp = tmpstream.str();
      if (tmp.size() > 0) {
        tmp = tmp.substr(0, tmp.size()-1);
      }
      cout << tmp << endl;
      machine = ll_next_obj(queryObject);
   }


   /* Free objects obtained from Negotiator */
   ll_free_objs(queryObject);
   /* Free query element */
   ll_deallocate(queryObject);
   return 0;
}

