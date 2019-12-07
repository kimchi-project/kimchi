#!/bin/bash

set -euxo pipefail

DISKS="gcloud compute disks"
IMAGES="gcloud compute images"
INSTANCES="gcloud compute instances"
VMX="https://compute.googleapis.com/compute/v1/projects/vm-options/global/licenses/enable-vmx"
DEFAULT_ZONE=us-central1-a

function createDisk() {
    #  Create disk
    #  
    #  $1: disk name
    #  $2: image project
    #  $3: image-family
    #  $4: zone
    zone=${4:-$DEFAULT_ZONE}

    diskName=$1
    ${DISKS} create $diskName \
             --image-project $2 \
             --image-family $3 \
             --size 20GB \
             --zone $zone
}

function createImage() {
    #  Create image with nested virtualization
    #
    #  $1: image name
    #  $2: disk name
    #  $3: zone
    zone=${3:-$DEFAULT_ZONE}

    imageName=$1
    ${IMAGES} create $imageName \
              --source-disk $2 \
              --source-disk-zone $zone \
              --licenses "${VMX}"
}

function createVM() {
    #  Create VM with nested virtualization
    #
    #  $1: VM name
    #  $2: image name
    #  $3: zone
    zone=${3:-$DEFAULT_ZONE}

    instanceName=$1
    ${INSTANCES} create $1 \
                 --zone $zone \
                 --min-cpu-platform "Intel Haswell" \
                 --image $2
}

# Entrypoint
#
#  $1: vm name
#  $2: image project
#  $3: image family
#  $4: zone
vmName=$1
imageProject=$2
imageFamily=$3
zone=${4:-$DEFAULT_ZONE}

# create disk   
diskName=$vmName-disk
createDisk $vmName-disk $imageProject $imageFamily $zone

# create image
imageName=$vmName-image
createImage $imageName $diskName $zone

# create vm
createVM $1 $imageName $zone
