#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "llapi.h"

main(int argc, char *argv[])
{
   LL_element *queryObject, *machine;
   int rc, obj_count, err_code;
   char **host_list;
   char ** ppcBuffer;
   char ** ppChar;

   if (argc != 2) {
     fprintf(stderr, "Error: wrong syntax\nSyntax: %s <nodename>\n", argv[0]);
     exit(1);
   }
   /* Initialize the query: Machine query */
   queryObject = ll_query(MACHINES);
   if (!queryObject) {
      printf("Query MACHINES: ll_query() returns NULL.\n"); exit(1);
   }

   host_list = (char **)malloc(2*sizeof(char *));
   host_list[0] = argv[1];
   host_list[1] = NULL;
   rc = ll_set_request(queryObject, QUERY_HOST, host_list, ALL_DATA);
   if (rc) {
      printf("Query MACHINES: ll_set_request() return code is non-zero.\n"); exit(1);
   }

   machine = ll_get_objs(queryObject, LL_CM, NULL, &obj_count, &err_code);
   if (machine == NULL) {
      fprintf(stderr, "Query MACHINES: ll_get_objs() returns NULL. Error code = %d\n", err_code);
      exit(1);
   }

   rc = ll_get_data(machine,LL_MachineStepList,&ppcBuffer);
   switch(rc) { 
     case 0:  
       if((ppcBuffer!=NULL)&&(ppcBuffer[0]!=NULL)) { 
         for(ppChar = ppcBuffer; *ppChar!=NULL; ppChar++) { 
           printf("%s\n", *ppChar); 
           free(*ppChar);
         } 
       }
       break; 
     default: fprintf(stderr,"Unknown error %d returned from ll_get_data()\n",rc); break; 
   } 

   ll_free_objs(queryObject);
   ll_deallocate(queryObject);
}

