## Project Kimchi REST API Specification

The Kimchi API provides all functionality to the application and may be used
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
* URIs begin with a '/' to indicate the root of the API.
    * Variable segments in the URI begin with a ':' and should replaced with the
      appropriate resource identifier.

### Collection: Virtual Machines

**URI:** /vms

**Methods:**

* **GET**: Retrieve a summarized list of all defined Virtual Machines
* **POST**: Create a new Virtual Machine
    * name *(optional)*: The name of the VM.  Used to identify the VM in this
      API.  If omitted, a name will be chosen based on the template used.
    * template: The URI of a Template to use when building the VM
    * storagepool *(optional)*: Assign a specific Storage Pool to the new VM

### Resource: Virtual Machine

**URI:** /vms/*:name*

**Methods:**

* **GET**: Retrieve the full description of a Virtual Machine
    * name: The name of the VM.  Used to identify the VM in this API
    * state: Indicates the current state in the VM lifecycle
        * running: The VM is powered on
        * paused: The VMs virtual CPUs are paused
        * shutoff: The VM is powered off
    * stats: Virtual machine statistics:
        * cpu_utilization: A number between 0 and 100 which indicates the
          percentage of CPU utilization.
        * net_throughput: Expresses total network throughput for reads and
          writes across all virtual interfaces (kb/s).
        * net_throughput_peak: The highest recent value of 'net_throughput'.
        * io_throughput: Expresses the total IO throughput for reads and
          writes across all virtual disks (kb/s).
        * io_throughput_peak: The highest recent value of 'io_throughput'.
    * memory: The amount of memory assigned to the VM (in MB)
    * screenshot: A link to a recent capture of the screen in PNG format
    * icon: A link to an icon that represents the VM
    * graphics: A dict to show detail of VM graphics.
        * type: The type of graphics, It can be VNC or None.
            * vnc: Graphical display using the Virtual Network
                   Computing protocol
            * null: Graphics is disabled or type not supported
        * port: The port number of graphics. It will remain None until a connect
                call is issued.
                The port number exposed will support the websockets protocol and
                may support graphics type over plain TCP as well.
* **DELETE**: Remove the Virtual Machine
* **POST**: *See Virtual Machine Actions*

**Actions (POST):**

* start: Power on a VM
* stop: Power off forcefully

### Sub-resource: Virtual Machine Screenshot

**URI:** /vms/*:name*/screenshot

Represents a snapshot of the Virtual Machine's primary monitor.

**Methods:**

* **GET**: Redirect to the latest screenshot of a Virtual Machine in PNG format

### Collection: Templates

**URI:** /templates

**Methods:**

* **GET**: Retrieve a summarized list of all defined Templates
* **POST**: Create a new Template
    * name: The name of the Template.  Used to identify the Template in this API


### Resource: Template

**URI:** /templates/*:name*

**Methods:**

* **GET**: Retrieve the full description of a Template
    * name: A name for this template
    * folder: A virtual path which can be used to organize Templates in a user
      interface.  The format is an array of path components.
    * icon: A URI to a PNG image representing this template
    * os_distro: The operating system distribution
    * os_version: The version of the operating system distribution
    * cpus: The number of CPUs assigned to the VM
    * memory: The amount of memory assigned to the VM
    * cdrom: A volume name or URI to an ISO image
    * disks: An array of requested disks with the following optional fields
      (either *size* or *volume* must be specified):
        * index: The device index
        * size: The device size in GB
        * volume: A volume name that contains the initial disk contents
* **DELETE**: Remove the Template
* **POST**: *See Template Actions*
* **PUT**: update the parameters of existed template
    * name: A name for this template
    * folder: A virtual path which can be used to organize Templates in the user
      interface.  The format is an array of path components.
    * icon: A URI to a PNG image representing this template
    * os_distro: The operating system distribution
    * os_version: The version of the operating system distribution
    * cpus: The number of CPUs assigned to the VM
    * memory: The amount of memory assigned to the VM
    * cdrom: A volume name or URI to an ISO image
    * disks: An array of requested disks with the following optional fields
      (either *size* or *volume* must be specified):
        * index: The device index
        * size: The device size in GB
        * volume: A volume name that contains the initial disk contents

**Actions (POST):**

* *No actions defined*

### Collection: Storage Pools

**URI:** /storagepools

**Methods:**

* **GET**: Retrieve a summarized list of all defined Storage Pools
* **POST**: Create a new Storage Pool
    * name: The name of the Storage Pool
    * path: The path of the defined Storage Pool
    * type: The type of the defined Storage Pool

### Resource: Storage Pool

**URI:** /storagepools/*:name*

**Methods:**

* **GET**: Retrieve the full description of a Storage Pool
    * name: The name of the Storage Pool
            Used to identify the Storage Pool in this API
            'kimchi_isos' is a reserved storage pool
            which aggregates all ISO images
            across all active storage pools into a single view.
    * state: Indicates the current state of the Storage Pool
        * active: The Storage Pool is ready for use
        * inactive: The Storage Pool is not available
    * path: The path of the defined Storage Pool
    * type: The type of the Storage Pool
    * capacity: The total space which can be used to store volumes
                The unit is MBytes
    * allocated: The amount of space which is being used to store volumes
                The unit is MBytes
    * available: Free space available for creating new volumes in the pool
    * nr_volumes: The number of storage volumes for active pools, 0 for inactive pools

* **DELETE**: Remove the Storage Pool
* **POST**: *See Storage Pool Actions*

**Actions (POST):**

* activate: Activate an inactive Storage Pool
* deactivate: Deactivate an active Storage Pool

### Collection: Storage Volumes

**URI:** /storagepools/*:poolname*/storagevolumes

**Methods:**

* **GET**: Retrieve a summarized list of all defined Storage Volumes
           in the defined Storage Pool
* **POST**: Create a new Storage Volume in the Storage Pool
    * name: The name of the Storage Volume
    * type: The type of the defined Storage Volume
    * capacity: The total space which can be used to store volumes
                The unit is MBytes
    * format: The format of the defined Storage Volume

### Resource: Storage Volume

**URI:** /storagepools/*:poolname*/storagevolumes/*:name*

**Methods:**

* **GET**: Retrieve the full description of a Storage Volume
    * name: The name of the Storage Volume
            Used to identify the Storage Volume in this API
    * type: The type of the Storage Volume
    * capacity: The total space which can be used to store data
                The unit is MBytes
    * allocation: The amount of space which is being used to store data
                The unit is MBytes
    * format: The format of the file or volume
    * path: Full path of the volume on the host filesystem.
    * os_distro *(optional)*: os distribution of the volume, for iso volume only.
    * os_version *(optional)*: os version of the volume, for iso volume only.
    * bootable *(optional)*: True if iso image is bootable and not corrupted.

* **DELETE**: Remove the Storage Volume
* **POST**: *See Storage Volume Actions*

**Actions (POST):**

* resize: Resize a Storage Volume
* wipe: Wipe a Storage Volume

### Collection: Tasks

**URI:** /tasks

**Methods:**

* **GET**: Retrieve a summarized list of current Tasks

### Resource: Task

**URI:** /tasks/*:id*

A task represents an asynchronous operation that is being performed by the
server.

**Methods:**

* **GET**: Retrieve the full description of the Task
    * id: The Task ID is used to identify this Task in the API.
    * status: The current status of the Task
        * running: The task is running
        * finished: The task has finished successfully
        * failed: The task failed
    * message: Human-readable details about the Task status
* **POST**: *See Task Actions*

**Actions (POST):**

*No actions defined*

### Resource: Configuration

**URI:** /config

Contains information about the application environment and configuration.

**Methods:**

* **GET**: Retrieve configuration information
    * http_port: The port number on which the server is listening
* **POST**: *See Configuration Actions*

**Actions (POST):**

*No actions defined*

### Resource: Capabilities

**URI:** /config/capabilities

Contains information about the host capabilities: iso streaming, screenshot
creation.

**Methods:**

* **GET**: Retrieve capabilities information
    * stream_protocols: list of which network protocols are accepted for iso
      streaming
    * screenshot: True, if libvirt stream functionality can create screenshot
      file without problems; False, otherwise or None if the functionality was
      not tested yet
* **POST**: *See Configuration Actions*

**Actions (POST):**

*No actions defined*
