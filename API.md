## Project Burnet REST API Specification

The Burnet API provides all functionality to the application and may be used
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
    * name: The name of the VM.  Used to identify the VM in this API
    * memory: The amount of memory assigned to the VM (in MB)

### Resource: Virtual Machine

**URI:** /vms/*:name*

**Methods:**

* **GET**: Retrieve the full description of a Virtual Machine
    * name: The name of the VM.  Used to identify the VM in this API
    * state: Indicates the current state in the VM lifecycle
        * running: The VM is powered on
        * paused: The VMs virtual CPUs are paused
        * shutoff: The VM is powered off
    * memory: The amount of memory assigned to the VM (in MB)
    * screenshot: A link to a recent capture of the screen in PNG format
* **DELETE**: Remove the Virtual Machine
* **POST**: *See Virtual Machine Actions*

**Actions (POST):**

* start: Power on a VM
* stop: Power off forcefully
