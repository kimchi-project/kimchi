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
* URIs begin with '/plugins/kimchi' to indicate the root of Kimchi plugin.
    * Variable segments in the URI begin with a ':' and should replaced with the
      appropriate resource identifier.


### Collection: Tasks

**URI:** /plugins/kimchi/tasks

**Methods:**

* **GET**: Retrieve a summarized list of current Kimchi specific Tasks (stored
in Kimchi's object store)

### Resource: Task

**URI:** /plugins/kimchi/tasks/*:id*

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

### Collection: Virtual Machines

**URI:** /plugins/kimchi/vms

**Methods:**

* **GET**: Retrieve a summarized list of all defined Virtual Machines
* **POST**: Create a new Virtual Machine
    * name *(optional)*: The name of the VM.  Used to identify the VM in this
      API.  If omitted, a name will be chosen based on the template used.
    * persistent: If 'true',  vm will persist after a Power Off or host reboot.
                  All virtual machines created by Kimchi are persistent.
    * template: The URI of a Template to use when building the VM
    * storagepool *(optional)*: Assign a specific Storage Pool to the new VM
    * graphics *(optional)*: Specify the graphics paramenter for this vm
        * type: The type of graphics. It can be VNC or spice or None.
            * vnc: Graphical display using the Virtual Network
                   Computing protocol
            * spice: Graphical display using the Simple Protocol for
                     Independent Computing Environments
            * null: Graphics is disabled or type not supported
        * listen: The network which the vnc/spice server listens on.


### Resource: Virtual Machine

**URI:** /plugins/kimchi/vms/*:name*

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
        * mem_utilization: A number between 0 and 100 which indicates the
          percentage of memory utilization.
        * net_throughput: Expresses total network throughput for reads and
          writes across all virtual interfaces (kb/s).
        * net_throughput_peak: The highest recent value of 'net_throughput'.
        * io_throughput: Expresses the total IO throughput for reads and
          writes across all virtual disks (kb/s).
        * io_throughput_peak: The highest recent value of 'io_throughput'.
    * uuid: UUID of the VM.
    * memory: The amount of memory assigned to the VM (in MB)
    * cpus: The number of CPUs assigned to the VM
    * screenshot: A link to a recent capture of the screen in PNG format
    * icon: A link to an icon that represents the VM
    * graphics: A dict to show detail of VM graphics.
        * type: The type of graphics. It can be VNC or spice or None.
            * vnc: Graphical display using the Virtual Network
                   Computing protocol
            * spice: Graphical display using the Simple Protocol for
                     Independent Computing Environments
            * null: Graphics is disabled or type not supported
        * listen: The network which the vnc/spice server listens on.
        * port: The real port number of the graphics, vnc or spice. Users
                can use this port to connect to the vm with general vnc/spice
                clients.
        * passwd: console password
        * passwdValidTo: lifetime for the console password.
    * users: A list of system users who have permission to access the VM.
      Default is: empty (i.e. only root-users may access).
    * groups: A list of system groups whose users have permission to access
      the VM. Default is: empty (i.e. no groups given access).
* **DELETE**: Remove the Virtual Machine
* **PUT**: update the parameters of existed VM
    * name: New name for this VM (only applied for shutoff VM)
    * users: New list of system users.
    * groups: New list of system groups.
    * cpus: New number of virtual cpus for this VM (if VM is running, new value
            will take effect in next reboot)
    * memory: New amount of memory (MB) for this VM (if VM is running, new
              value will take effect in next reboot)
    * graphics: A dict to show detail of VM graphics.
        * passwd *(optional)*: console password. When omitted a random password
                               willbe generated.
        * passwdValidTo *(optional)*: lifetime for the console password. When
                                      omitted the password will be valid just
                                      for 30 seconds.

* **POST**: *See Virtual Machine Actions*

**Actions (POST):**

* start: Power on a VM
* poweroff: Power off a VM forcefully. Note this action may produce undesirable
            results, for example unflushed disk cache in the guest.
* shutdown: Shut down a VM graceful. This action issue shutdown request to guest.
            And the guest will react this request. Note the guest OS may ignore
            the request.
* reset: Reset a VM immediately without the guest OS shutdown.
         It emulates the power reset button on a machine. Note that there is a
         risk of data loss caused by reset without the guest OS shutdown.
* connect: Prepare the connection for spice or vnc

* clone: Create a new VM identical to this VM. The new VM's name, UUID and
         network MAC addresses will be generated automatically. Each existing
         disks will be copied to a new volume in the same storage pool. If
         there is no available space on that storage pool to hold the new
         volume, it will be created on the pool 'default'. This action returns
         a Task.

* suspend: Suspend an active domain. The process is frozen without further
           access to CPU resources and I/O but the memory used by the domain at
           the hypervisor level will stay allocated.

* resume: Resume a suspended domain. The process is restarted from the state
          where it was frozen by calling "suspend".

* migrate: Migrate a virtual machine to a remote server, only support live
mode without block migration.
    * remote_host: IP address or hostname of the remote server.
    * user *(optional)*: User to log on at the remote server.
    * password *(optional)*: password of the user in the remote server.

### Sub-resource: Virtual Machine Screenshot

**URI:** /plugins/kimchi/vms/*:name*/screenshot

Represents a snapshot of the Virtual Machine's primary monitor.

**Methods:**

* **GET**: Redirect to the latest screenshot of a Virtual Machine in PNG format


### Sub-collection: Virtual Machine storages
**URI:** /plugins/kimchi/vms/*:name*/storages
* **GET**: Retrieve a summarized list of all storages of specified guest
* **POST**: Attach a new storage or virtual drive to specified virtual machine.
    * type: The type of the storage (currently support 'cdrom' and 'disk').
    * path: Path of cdrom iso.
    * pool: Storage pool which disk image file locate in.
    * vol: Storage volume name of disk image.

### Sub-resource: storage
**URI:** /plugins/kimchi/vms/*:name*/storages/*:dev*
* **GET**: Retrieve storage information
    * dev: The name of the storage in the vm.
    * type: The type of the storage (currently support 'cdrom' and 'disk').
    * path: Path of cdrom iso or disk image file.
    * bus: Bus type of disk attached.
* **PUT**: Update storage information
    * path: Path of cdrom iso. Can not be blank. Now just support cdrom type.
* **DELETE**: Remove the storage.

**Actions (POST):**


### Sub-collection: Virtual Machine Passthrough Devices
**URI:** /plugins/kimchi/vms/*:name*/hostdevs
* **GET**: Retrieve a summarized list of all directly assigned host device of
           specified guest.
* **POST**: Directly assign a host device to guest.
    * name: The name of the host device to be assigned to vm.

### Sub-resource: Device
**URI:** /plugins/kimchi/vms/*:name*/hostdevs/*:dev*
* **GET**: Retrieve assigned device information
    * name: The name of the assigned device.
    * type: The type of the assigned device.
* **DELETE**: Detach the host device from VM.

### Sub-collection: Virtual Machine Snapshots
**URI:** /plugins/kimchi/vms/*:name*/snapshots
* **POST**: Create a new snapshot on a VM.
    * name: The snapshot name (optional, defaults to a value based on the
            current time).
* **GET**: Retrieve a list of snapshots on a VM.

### Sub-resource: Snapshot
**URI:** /plugins/kimchi/vms/*:name*/snapshots/*:snapshot*
* **GET**: Retrieve snapshot information.
    * created: The time when the snapshot was created
               (in seconds, since the epoch).
    * name: The snapshot name.
    * parent: The name of the parent snapshot, or an empty string if there is
              no parent.
    * state: The corresponding domain's state when the snapshot was created.
* **DELETE**: Delete snapshot. If the snapshot has any children, they will be
              merged automatically with the snapshot's parent.
* **POST**: See "Snapshot actions (POST)"

**Snapshot Actions (POST):**

* revert: Revert the domain to the given snapshot.

### Sub-resource: Current snapshot
**URI:** /plugins/kimchi/vms/*:name*/snapshots/current
* **GET**: Retrieve current snapshot information for the virtual machine.

### Collection: Templates

**URI:** /plugins/kimchi/templates

**Methods:**

* **GET**: Retrieve a summarized list of all defined Templates
* **POST**: Create a new Template
    * name: The name of the Template.  Used to identify the Template in this API
    * os_distro *(optional)*: The operating system distribution
    * os_version *(optional)*: The version of the operating system distribution
    * cpus *(optional)*: The number of CPUs assigned to the VM.
          Default is 1, unlees specifying a cpu topology. In that case, cpus
          will default to a product of the topology values (see cpu_info).
    * memory *(optional)*: The amount of memory assigned to the VM.
      Default is 1024M.
    * cdrom *(optional)*: A volume name or URI to an ISO image.
    * storagepool *(optional)*: URI of the storagepool.
      Default is '/storagepools/default'
    * networks *(optional)*: list of networks will be assigned to the new VM.
      Default is '[default]'
    * disks *(optional)*: An array of requested disks with the following optional fields
      (either *size* or *volume* must be specified):
        * index: The device index
        * size: The device size in GB
        * base: Base image of this disk

    * graphics *(optional)*: The graphics paramenters of this template
        * type: The type of graphics. It can be VNC or spice or None.
            * vnc: Graphical display using the Virtual Network
                   Computing protocol
            * spice: Graphical display using the Simple Protocol for
                     Independent Computing Environments
            * null: Graphics is disabled or type not supported
        * listen: The network which the vnc/spice server listens on.
    * cpu_info *(optional)*: CPU-specific information.
        * topology: Specify sockets, threads, and cores to run the virtual CPU
            threads on.
            All three are required in order to specify cpu topology.
            * sockets - The number of sockets to use.
            * cores   - The number of cores per socket.
            * threads - The number of threads per core.
            If specifying both cpus and CPU topology, make sure cpus is
            equal to the product of sockets, cores, and threads.

### Sub-Collection: Virtual Machine Network Interfaces

**URI:** /plugins/kimchi/vms/*:name*/ifaces

Represents all network interfaces attached to a Virtual Machine.

**Methods:**

* **GET**: Retrieve a summarized list of all network interfaces attached to a Virtual Machine.

* **POST**: attach a network interface to VM
    * model *(optional)*: model of emulated network interface card. It can be one of these models:
            ne2k_pci, i82551, i82557b, i82559er, rtl8139, e1000, pcnet and virtio.
            When model is missing, libvirt will set 'rtl8139' as default value.
    * network *(optional)*: the name of resource network, it is required when the
              interface type is network.
    * type: The type of VM network interface that libvirt supports.
            Now kimchi just supports 'network' type.

### Sub-Resource: Virtual Machine Network Interface

**URI:** /plugins/kimchi/vms/*:name*/ifaces/*:mac*

A interface represents available network interface on VM.

**Methods:**

* **GET**: Retrieve the full description of the VM network interface
    * bridge *(optional)*: the name of resource bridge, only be available when the
              interface type is bridge.
    * mac: Media Access Control Address of the VM interface.
    * ips: A list of IP addresses associated with this MAC.
    * model *(optional)*: model of emulated network interface card. It will be one of these models:
             ne2k_pci, i82551, i82557b, i82559er, rtl8139, e1000, pcnet and virtio.
    * network *(optional)*: the name of resource network, only be available when the
              interface type is network.
    * type: The type of VM network interface that libvirt supports.
            It will be one of these types: 'network', 'bridge', 'user','ethernet',
            'direct', 'hostdev', 'mcast', 'server' and 'client'.

* **DELETE**: detach the network interface from VM

* **PUT**: update the parameters of existing VM interface.
    * model *(optional)*: model of emulated network interface card. It will be one of these models:
             ne2k_pci, i82551, i82557b, i82559er, rtl8139, e1000, pcnet and virtio.
             This change is only on the persisted VM configuration.
    * network *(optional)*: the name of resource network, only be available when the
              interface type is network.
              This change is on the active VM instance and persisted VM configuration.

**Actions (POST):**

*No actions defined*


### Resource: Template

**URI:** /plugins/kimchi/templates/*:name*

**Methods:**

* **GET**: Retrieve the full description of a Template
    * name: A name for this template
    * folder: A virtual path which can be used to organize Templates in a user
      interface.  The format is an array of path components.
    * icon: A URI to a PNG image representing this template
    * os_distro: The operating system distribution
    * os_version: The version of the operating system distribution
    * cpus: The number of CPUs assigned to the VM
    * memory: The amount of memory assigned to the VM in the unit of MB
    * cdrom: A volume name or URI to an ISO image
    * storagepool: URI of the storagepool where template allocates vm storage.
    * networks *(optional)*: list of networks will be assigned to the new VM.
    * disks: An array of requested disks with the following optional fields
      (either *size* or *volume* must be specified):
        * index: The device index
        * size: The device size in GB
        * volume: A volume name that contains the initial disk contents
        * format: Format of the image. Valid formats: bochs, cloop, cow, dmg, qcow, qcow2, qed, raw, vmdk, vpc.
    * graphics: A dict of graphics paramenters of this template
        * type: The type of graphics. It can be VNC or spice or None.
            * vnc: Graphical display using the Virtual Network
                   Computing protocol
            * spice: Graphical display using the Simple Protocol for
                     Independent Computing Environments
            * null: Graphics is disabled or type not supported
        * listen: The network which the vnc/spice server listens on.
    * invalid: A dict indicates which paramenters of this template are invalid.
        * networks *(optional)*: An array of invalid network names.
        * cdrom *(optional)*: An array of invalid cdrom names.
        * disks *(optional)*: An array of invalid volume names.
        * storagepools *(optional)*: An array of invalid storagepool names.

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
    * storagepool: URI of the storagepool where template allocates vm storage.
    * networks *(optional)*: list of networks will be assigned to the new VM.
    * disks: An array of requested disks with the following optional fields
      (either *size* or *volume* must be specified):
        * index: The device index
        * size: The device size in GB
        * volume: A volume name that contains the initial disk contents
        * format: Format of the image. Valid formats: bochs, cloop, cow, dmg, qcow, qcow2, qed, raw, vmdk, vpc.
    * graphics *(optional)*: A dict of graphics paramenters of this template
        * type: The type of graphics. It can be VNC or spice or None.
            * vnc: Graphical display using the Virtual Network
                   Computing protocol
            * spice: Graphical display using the Simple Protocol for
                     Independent Computing Environments
            * null: Graphics is disabled or type not supported
        * listen: The network which the vnc/spice server listens on.

**Actions (POST):**

* clone: clone a template from an existing template with different name.
         It will provide a reasonable default name with "-cloneN" as suffix
         for the new clone template. The "N" means the number of clone times.

### Collection: Storage Pools

**URI:** /plugins/kimchi/storagepools

**Methods:**

* **GET**: Retrieve a summarized list of all defined Storage Pools
* **POST**: Create a new Storage Pool
    * name: The name of the Storage Pool. It corresponds to the VG name while
            creating a logical storage pool from an existing VG.
    * type: The type of the defined Storage Pool.
            Supported types: 'dir', 'kimchi-iso', 'netfs', 'logical', 'iscsi', 'scsi'
    * path: The path of the defined Storage Pool.
            For 'kimchi-iso' pool refers to targeted deep scan path.
            Pool types: 'dir', 'kimchi-iso'.
    * source: Dictionary containing source information of the pool.
        * host: IP or hostname of server for a pool backed from a remote host.
                Pool types: 'netfs', 'iscsi'.
        * path: Export path on NFS server for NFS pool.
                Pool types: 'netfs'.
        * devices: Array of devices to be used in the Storage Pool
                   Pool types: 'logical'.
        * target: Target IQN of an iSCSI pool.
                  Pool types: 'iscsi'.
        * port *(optional)*: Listening port of a remote storage server.
                             Pool types: 'iscsi'.
        * auth *(optional)*: Storage back-end authentication information.
                             Pool types: 'iscsi'.
            * username: Login username of the iSCSI target.
            * password: Login password of the iSCSI target.
        * adapter_name: SCSI host name.
        * from_vg: Indicate if a logical pool will be created from an
                   existing VG or not.

### Resource: Storage Pool

**URI:** /plugins/kimchi/storagepools/*:name*

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
                The unit is Bytes
    * allocated: The amount of space which is being used to store volumes
                The unit is Bytes
    * available: Free space available for creating new volumes in the pool
    * nr_volumes: The number of storage volumes for active pools, 0 for inactive pools
    * autostart: Whether the storage pool will be enabled
                 automatically when the system boots
    * persistent: True, when pool persist after a system reboot or be stopped.
                  All storage pools created by Kimchi are persistent.
    * source: Source of the storage pool,
        * addr: mount address of this storage pool(for 'netfs' pool)
        * path: export path of this storage pool(for 'netfs' pool)

* **PUT**: Set whether the Storage Pool should be enabled automatically when the
           system boots
    * autostart: Toggle the autostart flag of the VM. This flag sets whether
                 the Storage Pool should be enabled automatically when the
                 system boots
    * disks: Adds one or more disks to the pool (for 'logical' pool only)
* **DELETE**: Remove the Storage Pool
* **POST**: *See Storage Pool Actions*

**Actions (POST):**

* activate: Activate an inactive Storage Pool
* deactivate: Deactivate an active Storage Pool

### Collection: Storage Volumes

**URI:** /plugins/kimchi/storagepools/*:poolname*/storagevolumes

**Methods:**

* **GET**: Retrieve a summarized list of all defined Storage Volumes
           in the defined Storage Pool
* **POST**: Create a new Storage Volume in the Storage Pool
            The return resource is a task resource * See Resource: Task *
            Only one of 'capacity', 'url' can be specified.
    * name: The name of the Storage Volume
    * capacity: The total space which can be used to store volumes
                The unit is bytes
    * format: The format of the defined Storage Volume. Only used when creating
              a storage volume with 'capacity'.
    * upload: True to start an upload process. False, otherwise.
              Only used when creating a storage volume 'capacity' parameter.
    * file: File to be uploaded, passed through form data

### Resource: Storage Volume

**URI:** /plugins/kimchi/storagepools/*:poolname*/storagevolumes/*:name*

**Methods:**

* **GET**: Retrieve the full description of a Storage Volume
    * name: The name of the Storage Volume
            Used to identify the Storage Volume in this API
    * type: The type of the Storage Volume
    * capacity: The total space which can be used to store data
                The unit is Bytes
    * allocation: The amount of space which is being used to store data
                The unit is Bytes
    * format: The format of the file or volume
    * path: Full path of the volume on the host filesystem.
    * os_distro *(optional)*: os distribution of the volume, for iso volume only.
    * os_version *(optional)*: os version of the volume, for iso volume only.
    * bootable *(optional)*: True if iso image is bootable and not corrupted.
    * used_by: Name of vms which use this volume.
    * isvalid: True if is a valid volume.

* **DELETE**: Remove the Storage Volume
* **POST**: *See Storage Volume Actions*
* **PUT**: Upload storage volume chunk
    * chunk_size: Chunk size of the slice in Bytes.
    * chunk: Actual data of uploaded file

**Actions (POST):**

* resize: Resize a Storage Volume
    * size: resize the total space which can be used to store data
            The unit is bytes
* wipe: Wipe a Storage Volume
* clone: Clone a Storage Volume.
    * pool: The name of the destination pool (optional).
    * name: The new storage volume name (optional).


### Collection: Interfaces

**URI:** /plugins/kimchi/interfaces

**Methods:**

* **GET**: Retrieve a summarized list of current Interfaces

### Resource: Interface

**URI:** /plugins/kimchi/interfaces/*:name*

A interface represents available interface on host.

**Methods:**

* **GET**: Retrieve the full description of the Interface
    * name: The name of the interface.
    * status: The current status of the Interface.
        * active: The interface is active.
        * inactive: The interface is inactive.
    * ipaddr: The ip address assigned to this interface in subnet.
    * netmask: Is used to divide an IP address into subnets and specify the
               networks available hosts
    * type: The net device type of the interface.
       * nic: Network interface controller that connects a computer to a
              computer network
       * vlan: A logical interface that represents a VLAN in all Layer 3
               activities the unit may participate in
       * bonding: The combination of network interfaces on one host for redundancy
                  and/or increased throughput.
       * bridge: A network device that connects multiple network segments.

* **POST**: *See Interface Actions*

**Actions (POST):**

*No actions defined*

### Collection: Networks

**URI:** /plugins/kimchi/networks

**Methods:**

* **GET**: Retrieve a summarized list of all defined Networks
* **POST**: Create a new Network
    * name: The name of the Network
    * connection: Specifies how this network should be connected to the other
                  networks visible to this host.
        * isolated: Create a private, isolated virtual network.
        * nat: Outgoing traffic will be routed through the host.
        * macvtap: All traffic on this network will be bridged through the
                   specified interface.
        * bridge: All traffic on this network will be bridged through a Linux
                  bridged, which is created upon specified interface in case
                  it is not already a Linux bridge.
    * subnet *(optional)*: Network segment in slash-separated format with ip address and
                           prefix or netmask used to create nat network.
    * interface *(optional)*: The name of a network interface on the host.
                              For "macvtap" and "bridge" connections, the
                              interface can be a nic, bridge or bonding device.
    * vlan_id *(optional)*: VLAN tagging ID for the macvtap bridge network.

### Resource: Network

**URI:** /plugins/kimchi/networks/*:name*

**Methods:**

* **GET**: Retrieve the full description of a Network
    * name: The name of the Network
            Used to identify the Network in this API
    * state: Indicates the current state of the Network
        * active: The Network is ready for use
        * inactive: The Network is not available
    * autostart: Network autostart onboot
    * in_use: Indicates ('true') if some guest is attached to this network and 'false' otherwise.
    * vms: all vms attached to this network
    * subnet: Network segment in slash-separated format with ip address and prefix
    * dhcp: DHCP services on the virtual network is enabled.
        * start: start boundary of a pool of addresses to be provided to DHCP clients.
        * end: end boundary of a pool of addresses to be provided to DHCP clients.
    * connection: Specifies how this network should be connected to the other networks
                  visible to this host.
        * isolated: A private, isolated virtual network.
                    The VMs attached to it can not be reached by the systems
                    outside of this network and vice versa.
        * nat: Outgoing traffic will be routed through the host.
               The VM attached to it will have internet access via the host but
               other computers will not be able to connect to the VM.
        * bridge: Aggregated Public Network.
                  The VM that joines this network is seen as a peer on this network
                  and it may offer network services such as HTTP or SSH.
    * interface: The name of a bridge network interface on the host.  All traffic
                 on this network will be bridged through the indicated interface.
                 The interface is a bridge or ethernet/bonding device.
    * persistent: If 'true', network will persist after a system reboot or be stopped.
                  All networks created by Kimchi are persistent.

* **DELETE**: Remove the Network
* **POST**: *See Network Actions*

**Actions (POST):**

* activate: Activate an inactive Network
* deactivate: Deactivate an active Network


### Resource: Configuration

**URI:** /plugins/kimchi/config

Contains information about the application environment and configuration.

**Methods:**

* **GET**: Retrieve configuration information
    * display_proxy_port: Port for vnc and spice's websocket proxy to listen on
    * version: The version of the kimchi service
* **POST**: *See Configuration Actions*

**Actions (POST):**

*No actions defined*

### Resource: Capabilities

**URI:** /plugins/kimchi/config/capabilities

Contains information about the host capabilities: iso streaming, screenshot
creation.

**Methods:**

* **GET**: Retrieve capabilities information
    * libvirt_stream_protocols: list of which network protocols are accepted
      for iso streaming by libvirt
    * qemu_spice: True, if QEMU supports Spice; False, otherwise
    * qemu_stream: True, if QEMU supports ISO streaming; False, otherwise
    * screenshot: True, if libvirt stream functionality can create screenshot
      file without problems; False, otherwise or None if the functionality was
      not tested yet
    * system_report_tool: True if the is some debug report tool installed on
      the system; False, otherwise.
    * update_tool: True if there is a compatible package manager for the
      system; False, otherwise
    * repo_mngt_tool: 'deb', 'yum' or None - when the repository management
      tool is not identified
    * federation: 'on' if federation feature is enabled, 'off' otherwise.
    * auth: authentication type, 'pam' and 'ldap' are supported.
* **POST**: *See Configuration Actions*

**Actions (POST):**

*No actions defined*

### Collection: Storage Servers

**URI:** /plugins/kimchi/storageservers

**Methods:**

* **GET**: Retrieve a summarized list of used storage servers.
    * Parameters:
        * _target_type: Filter server list with given type, currently support
                        'netfs' and 'iscsi'.

### Resource: Storage Server

**URI:** /plugins/kimchi/storageservers/*:host*

**Methods:**

* **GET**: Retrieve description of a Storage Server
    * host: IP or host name of storage server
    * port: port of storage server, only for "iscsi"

### Collection: Storage Targets

**URI:** /plugins/kimchi/storageservers/*:name*/storagetargets

**Methods:**

* **GET**: Retrieve a list of available storage targets.
    * Parameters:
        * _target_type: Filter target list with given type, currently support
                        'netfs' and 'iscsi'.
        * _server_port: Filter target list with given server port,
                        currently support 'iscsi'.
    * Response: A list with storage targets information.
        * host: IP or host name of storage server of this target.
        * target_type: Type of storage target, supported: 'nfs'.
        * target: Storage target path.

### Collection: Distros

**URI:** /plugins/kimchi/config/distros

**Methods:**

* **GET**: Retrieve a summarized list of all Distros

### Resource: Distro

**URI:** /plugins/kimchi/config/distros/*:name*

Contains information about the OS distribution.

**Methods:**

* **GET**: Retrieve a OS distribution information.
    * name: The name of the Distro.
    * os_distro: The operating system distribution.
    * os_version: The version of the operating system distribution.
    * path: A URI to an ISO image.

**Actions (POST):**

*No actions defined*

### Resource: Users

**URI:** /plugins/kimchi/users
List of available users.

**Methods:**

* **GET**: Retrieve list of available users.
    * Parameters:
        * _user_id: Validate whether user exists.
                    Essential for 'ldap' authentication.

### Resource: Groups

**URI:** /plugins/kimchi/groups
List of available groups.

**Methods:**

* **GET**: Retrieve list of available groups, only support 'pam' authentication.

### Collection: Devices

**URI:** /plugins/kimchi/host/devices

**Methods:**

* **GET**: Retrieves list of host devices (Node Devices).
    * Parameters:
        * _cap: Filter node device list with given node device capability.
                To list Fibre Channel SCSI Host devices, use "_cap=fc_host".
                Other available values are "fc_host", "net", "pci", "scsi",
                "storage", "system", "usb" and "usb_device".
        * _passthrough: Filter devices eligible to be assigned to guest
                        directly. Possible values are "ture" and "false".
        * _passthrough_affected_by: Filter the affected devices in the same
                                    group of a certain directly assigned device.
                                    The value should be the name of a device.
        * _available_only: Filter to list only the host devices that are not
                           attached to a VM.

### Resource: Device

**URI:** /plugins/kimchi/host/devices/*:name*

**Methods:**

* **GET**: Retrieve information of a single host device.
    * device_type: Type of the device, supported types are "net", "pci", "scsi",
                   "storage", "system", "usb" and "usb_device".
    * name: The name of the device.
    * path: Path of device in sysfs.
    * parent: The name of the parent parent device.
    * adapter: Host adapter information of a "scsi_host" or "fc_host" device.
        * type: The capability type of the scsi_host device (fc_host, vport_ops).
        * wwnn: The HBA Word Wide Node Name. Empty if pci device is not fc_host.
        * wwpn: The HBA Word Wide Port Name. Empty if pci device is not fc_host.
    * domain: Domain number of a "pci" device.
    * bus: Bus number of a "pci" device.
    * slot: Slot number of a "pci" device.
    * function: Function number of a "pci" device.
    * vendor: Vendor information of a "pci" device.
        * id: Vendor id of a "pci" device.
        * description: Vendor description of a "pci" device.
    * product: Product information of a "pci" device.
        * id: Product id of a "pci" device.
        * description: Product description of a "pci" device.
    * iommuGroup: IOMMU group number of a "pci" device. Would be None/null if
	              host does not enable IOMMU support.


### Sub-collection: VMs with the device assigned.
**URI:** /plugins/kimchi/host/devices/*:name*/vmholders
* **GET**: Retrieve a summarized list of all VMs holding the device.

### Sub-resource: VM holder
**URI:** /plugins/kimchi/host/devices/*:name*/vmholders/*:vm*
* **GET**: Retrieve information of the VM which is holding the device
    * name: The name of the VM.
    * state: The power state of the VM. Could be "running" and "shutdown".


### Collection: Partitions

**URI:** /plugins/kimchi/host/partitions

**Methods:**

* **GET**: Retrieves a detailed list of all partitions of the host.

### Resource: Partition

**URI:** /plugins/kimchi/host/partitions/*:name*

**Methods:**

* **GET**: Retrieve the description of a single Partition:
    * name: The name of the partition. Used to identify it in this API
    * path: The device path of this partition.
    * type: The type of the partition:
        * part: a standard partition
        * lvm: a partition that belongs to a lvm
    * fstype: The file system type of the partition
    * size: The total size of the partition, in bytes
    * mountpoint: If the partition is mounted, represents the mountpoint.
      Otherwise blank.
    * available: false, if the partition is in use by system; true, otherwise.

### Collection: Volume Groups

**URI:** /plugins/kimchi/host/vgs

**Methods:**

* **GET**: Retrieves a detailed list of all volume groups in the host.

### Resource: Volume Group

**URI:** /plugins/kimchi/host/vgs/*:name*

**Methods:**

* **GET**: Retrieve the description of a single Volume Group:
    * name: The volume group name. Used to identify it in this API.
    * lvs: The logical volumes associated to this volume group.
    * pvs: The phisical volumes associated to this volume group.
    * free: Amount of free space in the volume group.
    * size: Total size of the volume group.

### Collection: Peers

**URI:** /plugins/kimchi/peers

**Methods:**

* **GET**: Return the list of Kimchi peers in the same network
           (It uses openSLP for discovering)
