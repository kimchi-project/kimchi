## Project Gigner Base REST API Specification

The Ginger Base API provides all functionality to the application and may be used
directly by external tools.  In the following sections you will find the
specification of all Collections and Resource types that are supported and the
URIs where they can be accessed.  In order to use the API effectively, please
the following general conventions:

* The **Content Type** of the API is JSON.  When making HTTP requests to this
  API you should specify the following headers:
    * Accept: application/json
    * Content-type: application/json
* A **Collection** is a group of Resources of a given type.
    * A **GET** request retrieves a list of summarized Resource representations
      This summary *may* include all or some of the Resource properties but
      *must* include a link to the full Resource representation.
    * A **POST** request will create a new Resource in the Collection. The set
      of Resource properties *must* be specified as a JSON object in the request
      body.
    * No other HTTP methods are supported for Collections
* A **Resource** is a representation of a singular object in the API (eg.
  Virtual Machine).
    * A **GET** request retrieves the full Resource representation.
    * A **DELETE** request will delete the Resource. This request *may* contain
      a JSON object which specifies optional parameters.
    * A **PUT** request is used to modify the properties of a Resource (eg.
      Change the name of a Virtual Machine). This kind of request *must not*
      alter the live state of the Resource. Only *actions* may alter live state.
    * A **POST** request commits an *action* upon a Resource (eg. Start a
      Virtual Machine). This request is made to a URI relative to the Resource
      URI. Available *actions* are described within the *actions* property of a
      Resource representation.  The request body *must* contain a JSON object
      which specifies parameters.
* URIs begin with '/plugins/gingerbase' to indicate the root of gingerbase plugin.
    * Variable segments in the URI begin with a ':' and should replaced with the
      appropriate resource identifier.

#### Collection: Debug Reports

**URI:** /plugins/gingerbase/debugreports

**Methods:**

* **GET**: Retrieve a summarized list of all available Debug Reports
* **POST**: Create a new Debug Report. This POST method is different
      from the other ones. The return resource is a task resource which
      is identified by the url below
    * task resource.  * See Resource: Task *

### Resource: Debug Report

**URI:** /plugins/gingerbase/debugreports/*:name*

A Debug Report is an archive of logs and other information about the host that
is used to diagnose and debug problems. The exact format and contents are
specific to the low level collection tool being used.

**Methods:**

* **GET**: Retrieve the full description  of Debug Report
    * name: The debug report  name used to identify the report
    * uri: The URI path to download a debug report
    * time: The time when the debug report is created

* **PUT**: rename an existed debug report
    * name: The new name for this debug report

* **DELETE**: Remove the Debug Report
    * name: The debug report  name used to identify the report

* **POST**: *See Debug Report Actions*

**Actions (POST):**

*No actions defined*

### Sub-resource: Debug Report content

**URI:** /plugins/gingerbase/debugreports/*:name*/content

It is the sub-resource of Debug Report and the client use it to get the real content
of the Debug Report file from the server

* **GET**: Retrieve the content of a Debug Report file

**Actions (POST):**

*No actions defined*

### Resource: Host

**URI:** /plugins/gingerbase/host
Contains information of host.

**Methods:**

* **GET**: Retrieve host static information
    * memory: Total size of host physical memory
              The unit is Bytes
    * cpu_model: The model name of host CPU
    * cpus: The number of online CPUs available on host
    * os_distro: The OS distribution that runs on host
    * os_version: The version of OS distribution
    * os_codename: The code name of OS distribution

* **POST**: *See Host Actions*

**Actions (POST):**

* reboot: Restart the host machine.
          Only allowed if there is not vm running.
* shutdown: Power off the host machine.
            Only allowed if there is not vm running.
* swupdate: Start the update of packages in background and return a Task resource
    * task resource.  * See Resource: Task *

### Resource: HostStats

**URI:** /plugins/gingerbase/host/stats

Contains the host sample data.

**Methods:**

* **GET**: Retrieve host sample data
    * cpu_utilization: A number between 0 and 100 which indicates the
                       percentage of CPU utilization.
    * memory: memory statistics of host
        * total: Total amount of memory. The unit is Bytes.
        * free: The amount of memory left unused by the system. The unit is Bytes.
        * buffers: The amount of memory used for file buffers. The unit is Bytes.
        * cached: The amount of memory used as cache memory. The unit is Bytes.
        * avail: The total amount of buffer, cache and free memory. The unit is Bytes.
    * disk_read_rate: Expresses the total IO throughput for reads across
                      all disks (B/s).
    * disk_write_rate: Expresses the total IO throughput for writes across
                       all disks (B/s).
    * net_sent_rate: Expresses the total network throughput for writes across
                     all interfaces (B/s).
    * net_recv_rate: Expresses the total network throughput for reads across
                     all interfaces (B/s).

* **POST**: *See HostStats Actions*

**Actions (POST):**

*No actions defined*

### Resource: HostStats

**URI:** /plugins/gingerbase/host/cpuinfo

The cores and sockets of a hosts's CPU. Useful when sizing VMs to take
advantages of the perforamance benefits of SMT (Power) or Hyper-Threading (Intel).

**Methods:**

* **GET**: Retreives the sockets, cores, and threads values.
    * threading_enabled: Whether CPU topology is supported on this system.
    * sockets: The number of total sockets on a system.
    * cores: The total number of cores per socket.
    * threads_per_core: The threads per core.

**Actions (PUT):**

*No actions defined*

**Actions (POST):**

*No actions defined*

### Resource: HostStatsHistory

**URI:** /plugins/gingerbase/host/stats/history

It is the sub-resource of Host Stats and the client uses it to get the host
stats history

**Methods:**

* **GET**: Retrieve host sample data history
    * cpu_utilization: CPU utilization history
    * memory: Memory statistics history
        * total: Total amount of memory. The unit is Bytes.
        * free: The amount of memory left unused by the system. The unit is Bytes.
        * buffers: The amount of memory used for file buffers. The unit is Bytes.
        * cached: The amount of memory used as cache memory. The unit is Bytes.
        * avail: The total amount of buffer, cache and free memory. The unit is Bytes.
    * disk_read_rate: IO throughput for reads history
    * disk_write_rate: IO throughput for writes history
    * net_sent_rate: Network throughput for writes history
    * net_recv_rate: Network throughput for reads history

* **POST**: *See HostStatsHistory Actions*

**Actions (POST):**

*No actions defined*

### Collection: Host Packages Update

**URI:** /plugins/gingerbase/host/packagesupdate

Contains the information and action of packages update in the host.

**Methods:**

* **GET**: Retrieves a list of all packages to be updated in the host:

### Resource: Host Package Update

**URI:** /plugins/gingerbase/host/packagesupdate/*:name*

Contains the information for a specific package to be updated.

**Methods:**

* **GET**: Retrieves a full description of a package:
    * package_name: The name of the package to be updated
    * arch: The architecture of the package
    * version: The new version of the package
    * repository: The repository name from where package will be downloaded

### Collection: Host Repositories

**URI:** /plugins/gingerbase/host/repositories

**Methods:**

* **GET**: Retrieve a summarized list of all repositories available
* **POST**: Add a new repository
    * baseurl: URL to the repodata directory when "is_mirror" is false.
Otherwise, it can be URL to the mirror system for YUM. Can be an
http://, ftp:// or file://  URL.
    * repo_id *(optional)*: Unique YUM repository ID
    * config: A dictionary that contains specific data according to repository
      type.
        * repo_name *(optional)*: YUM Repository name
        * mirrorlist *(optional)*: Specifies a URL to a file containing a
          list of baseurls for YUM repository
        * dist: Distribution to DEB repository
        * comps *(optional)*: List of components to DEB repository

### Resource: Repository

**URI:** /plugins/gingerbase/host/repositories/*:repo-id*

**Methods:**

* **GET**: Retrieve the full description of a Repository
    * repo_id: Unique repository name for each repository, one word.
    * baseurl: URL to the repodata directory when "is_mirror" is false.
Otherwise, it can be URL to the mirror system for YUM. Can be an
http://, ftp:// or file://  URL.
    * enabled: True, when repository is enabled; False, otherwise
    * config: A dictionary that contains specific data according to repository
      type.
        * repo_name: Human-readable string describing the YUM repository.
        * mirrorlist: Specifies a URL to a file containing a list of baseurls
          for YUM repository
        * gpgcheck: True, to enable GPG signature verification; False, otherwise.
        * gpgkey: URL pointing to the ASCII-armored GPG key file for the YUM
          repository.
        * dist: Distribution to DEB repository
        * comps: List of components to DEB repository

* **DELETE**: Remove the Repository
* **POST**: *See Repository Actions*
* **PUT**: update the parameters of existing Repository
    * repo_id: Unique repository name for each repository, one word.
    * baseurl: URL to the repodata directory when "is_mirror" is false.
Otherwise, it can be URL to the mirror system for YUM. Can be an
http://, ftp:// or file://  URL.
    * config: A dictionary that contains specific data according to repository
      type.
        * repo_name: Human-readable string describing the YUM repository.
        * mirrorlist: Specifies a URL to a file containing a list of baseurls
          for YUM repository
        * gpgcheck: True, to enable GPG signature verification; False, otherwise.
        * gpgkey: URL pointing to the ASCII-armored GPG key file for the YUM
          repository.
        * dist: Distribution to DEB repository
        * comps: List of components to DEB repository

**Actions (POST):**

* enable: Enable the Repository as package source
* disable: Disable the Repository as package source
