#
# Project Kimchi
#
# Copyright IBM, Corp. 2015
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA

import lxml.etree as ET
from lxml.builder import E


def get_numa_xml(cpus, memory):
    # Returns the NUMA xml to be add into CPU element
    # Currently, supports only one node/cell
    #    <numa>
    #      <cell id='0' cpus='0-3' memory='512000' unit='KiB'/>
    #    </numa>
    xml = E.numa(E.cell(
        id='0',
        cpus='0-' + str(cpus - 1) if cpus > 1 else '0',
        memory=str(memory),
        unit='KiB'))
    return ET.tostring(xml)


def get_topology_xml(cpu_topo):
    # Return the cpu TOPOLOGY element
    #    <topology sockets='1' cores='2' threads='1'/>
    xml = E.topology(
        sockets=str(cpu_topo['sockets']),
        cores=str(cpu_topo['cores']),
        threads=str(cpu_topo['threads']))
    return ET.tostring(xml)


def get_cpu_xml(cpus, memory, cpu_topo=None):
    # Returns the libvirt CPU element based on given numa and topology
    # CPU element will always have numa element
    #   <cpu>
    #      <numa>
    #         <cell id='0' cpus='0-3' memory='512000' unit='KiB'/>
    #      </numa>
    #      <topology sockets='1' cores='2' threads='1'/>
    #   </cpu>
    xml = E.cpu(ET.fromstring(get_numa_xml(cpus, memory)))
    if cpu_topo is not None:
        xml.insert(0, ET.fromstring(get_topology_xml(cpu_topo)))
    return ET.tostring(xml)
