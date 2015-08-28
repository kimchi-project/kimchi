## Wok REST API Specification

The API provides functionality to the application and may be used directly by
external tools.  In the following sections you will find the specification of
all Collections and Resource types that are supported and the URIs where they
can be accessed.  In order to use the API effectively, please the following
general conventions:

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
* URIs begin with '/' to indicate Wok server root.
    * Variable segments in the URI begin with a ':' and should replaced with the
      appropriate resource identifier.


### Collection: Plugins

**URI:** /plugins

**Methods:**

* **GET**: Retrieve a summarized list names of all UI Plugins

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
    * target_uri: Resource URI related to the Task
* **POST**: *See Task Actions*

**Actions (POST):**

*No actions defined*
