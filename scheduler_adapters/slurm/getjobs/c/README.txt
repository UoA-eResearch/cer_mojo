Prerequisites:
 * build slurm from source go generate libslurm.o
   in slurm source base directory, run the following:

     ./configure --sysconfdir=/etc/slurm --libdir=/usr/lib64 
     make

   as soon as libslurm.o has been built src/api/ the make
   command can be stopped

   Notes:
    * sysconfdir is required to make the code look into /etc/slurm
      for configuration file. otherwise it'll look in /usr/local/etc,
      and there is no configuration file
    * libdir is required to make the code find the plugin directory

