scheduler_command_prefix = 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i /etc/apache2/ssh/id_rsa mfel395@10.0.103.76'
ganglia_main_page = 'http://ganglia.uoa.nesi.org.nz/?c=University%20of%20Auckland%20HPC%20Cluster'
ganglia_gmond_aggregator = 'localhost'
ganglia_gmond_port = '8649'
ganglia_blacklist = [ 'pan-ganglia-p', 'login-p', 'xcat-p', 'gpfs-a3-001-p', 'gpfs-a3-002-p', 'gpfs-a3-003-p', 'gpfs-a3-004-p' ]
