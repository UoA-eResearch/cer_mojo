mojo (MOnitor JObs)
===

Display information about jobs run on the Auckland NeSI cluster (managed by LoadLeveler) in a web-based format.
Information about jobs is gathered from scheduler adapater scripts and Ganglia (running processes).

The project consists of

* A cgi-based web interface (CGI scripts, JavaScript, CSS)
* LoadLeveler scheduler adapters to get information about jobs.


Installation Instructions
===

1. Configure Python package "cluster"
Configure the LRM in the configuration file python/cluster/cluster/config.py.
Set the value of 'main_ganglia_page' to your ganglia website.
2. Install Python package "cluster"
```
cd python/cluster
python setup.py install
```
3. Install the JavaScript files and CSS stylesheets
The JavaScript files and CSS stylesheets are expected to be located in the directory 'jobs' of the webservers
base website directory (document root).
(The following commands use ${DOCUMENT_ROOT} as the base website directory)
```
mkdir -p ${DOCUMENT_ROOT}/jobs/js 
mkdir -p ${DOCUMENT_ROOT}/jobs/style
cp -r style/* ${DOCUMENT_ROOT}/jobs/style/
cp -r js/* ${DOCUMENT_ROOT}/jobs/js/
```
If the location for JavaScript and CSS files needs to be different from /jobs, the paths to JavaScript and CSS files
must be adjusted in the scripts in the directory "cgi"
4. Install the CGI scripts
Copy the scripts in cgi/ into the cgi-bin directory of the webserver.
5. Install the scheduler adapter scripts 


Supported Python Versions
===

Tested with Python 2.4. Will probably work with all newer versions of Python.


Run tests
=========

This project doesn't contain an extensive test suite, but a few test-cases exist for important utility functions.

'nose' has to be installed in order to run the tests.

Run the tests:

```
cd python/cluster
nosetests
```
