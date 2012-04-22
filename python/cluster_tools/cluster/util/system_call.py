import sys
import shlex
import subprocess

def execute(command_and_args, error_on_stderr=True, error_on_nonzero_rc=True):
  ''' Run a system call '''
  try:
    process = subprocess.Popen(shlex.split(command_and_args), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout,stderr) = process.communicate()
  except:
    raise Exception("Failed to execute '%s': %s" % (command_and_args,sys.exc_info()[1]))
  rc = process.returncode
  if rc != 0 and error_on_nonzero_rc:
    raise Exception('\'%s\' returned exit code %d. stderr: %s' % (command_and_args,rc,stderr))
  if stderr != "" and error_on_stderr:
    raise Exception('Error executing command \'%s\': Got non-empty stderr: %s' % (command_and_args,stderr))
  return (stdout,stderr,rc)
