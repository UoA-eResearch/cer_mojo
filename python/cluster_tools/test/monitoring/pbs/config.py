# Array of testcases.
testdata = [
 {
   'queue': {
     'showq_output': 'showq output...',
     'expected': {
     }
   },
   'node': {
     'compute-59': {
       'qmgr_output': 'qmgr output...',
       'expected': {
         'phys_mem_gb': '',
         'cores': ''
       }
     }
   },
   'job': {
     '12345': {
       'checkjob_output': '... some checkjob output...',
       'qstat_output': '... some qstat output...',
       'expected': {
         'req_cores': '',
         'req_mem_gb': ''
       }
     }
   }
 }
]

