# -*- coding: utf-8 -*-
#
# Project Kimchi
#
# Copyright IBM Corp, 2016
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
import json
import os
import shutil
import tempfile
import time
import unittest

import iso_gen
import libvirt
from wok.plugins.kimchi.model import model
from wok.rollbackcontext import RollbackContext

import tests.utils as utils


TMP_DIR = '/var/lib/kimchi/tests/'
UBUNTU_ISO = TMP_DIR + 'ubuntu14.04.iso'
TMP_EVENT = None
EVENT_ID = 0


def setUpModule():
    global TMP_DIR, TMP_EVENT

    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    TMP_EVENT = tempfile.mktemp()

    iso_gen.construct_fake_iso(UBUNTU_ISO, True, '14.04', 'ubuntu')


def tearDownModule():
    global TMP_DIR, TMP_EVENT

    if os.path.exists(TMP_EVENT):
        os.unlink(TMP_EVENT)
    shutil.rmtree(TMP_DIR)


def _get_next_event_id():
    global EVENT_ID
    EVENT_ID += 1
    return EVENT_ID


def _get_event_id():
    global EVENT_ID
    return EVENT_ID


def _store_event(data):
    global TMP_EVENT
    with open(TMP_EVENT, 'a') as file:
        file.write('%s\n' % data)


def _get_event(id):
    global TMP_EVENT
    with open(TMP_EVENT, 'r') as file:
        for event in [line.rstrip('\n') for line in file.readlines()]:
            fields = event.split('|')
            if fields[0] == str(id):
                return fields[1]


class LibvirtEventsTests(unittest.TestCase):
    def setUp(self):
        self.tmp_store = tempfile.mktemp()

    def tearDown(self):
        os.unlink(self.tmp_store)

    def domain_event_lifecycle_cb(self, conn, dom, event, detail, *args):
        """
        Callback to handle Domain (VMs) events - VM Livecycle.
        """
        evStrings = (
            'Defined',
            'Undefined',
            'Started',
            'Suspended',
            'Resumed',
            'Stopped',
            'Shutdown',
            'PMSuspended',
            'Crashed',
        )
        evDetails = (
            ('Added', 'Updated'),
            ('Removed',),
            ('Booted', 'Migrated', 'Restored', 'Snapshot', 'Wakeup'),
            (
                'Paused',
                'Migrated',
                'IOError',
                'Watchdog',
                'Restored',
                'Snapshot',
                'API error',
            ),
            ('Unpaused', 'Migrated', 'Snapshot'),
            (
                'Shutdown',
                'Destroyed',
                'Crashed',
                'Migrated',
                'Saved',
                'Failed',
                'Snapshot',
            ),
            ('Finished',),
            ('Memory', 'Disk'),
            ('Panicked'),
        )

        data = {
            'domain': dom.name(),
            'event': evStrings[event],
            'event_detail': evDetails[event][detail],
        }
        _store_event('%s|%s' % (_get_next_event_id(), json.dumps(data)))

    @unittest.skipUnless(
        utils.running_as_root() and os.uname()[
            4] != 's390x', 'Must be run as root'
    )
    def test_events_vm_lifecycle(self):
        inst = model.Model(objstore_loc=self.tmp_store)
        self.objstore = inst.objstore
        conn = inst.conn.get()

        # Create a template and VM to test, and start lifecycle tests
        with RollbackContext() as rollback:
            # Register the most common Libvirt domain events to be handled.
            event_map = [
                (libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, self.domain_event_lifecycle_cb)
            ]

            for event, event_cb in event_map:
                conn.domainEventRegister(event_cb, None)
                rollback.prependDefer(conn.domainEventDeregister, event_cb)

            # Create a template
            template_params = {
                'name': 'ttest',
                'source_media': {'type': 'disk', 'path': UBUNTU_ISO},
            }

            inst.templates_create(template_params)
            rollback.prependDefer(inst.template_delete, 'ttest')

            # Create a VM (guest)
            vm_params = {
                'name': 'kimchi-vm1',
                'template': '/plugins/kimchi/templates/ttest',
            }
            task = inst.vms_create(vm_params)
            inst.task_wait(task['id'], 10)
            task = inst.task_lookup(task['id'])
            self.assertEqual('finished', task['status'])
            time.sleep(5)
            # Check event of domain definition (addition)
            res = json.loads(_get_event(str(_get_event_id())))
            self.assertEqual('kimchi-vm1', res['domain'])
            self.assertEqual('Defined', res['event'])
            self.assertEqual('Added', res['event_detail'])

            # Start the VM and check the event
            inst.vm_start('kimchi-vm1')
            time.sleep(5)
            res = json.loads(_get_event(str(_get_event_id())))
            self.assertEqual('kimchi-vm1', res['domain'])
            self.assertEqual('Started', res['event'])
            self.assertEqual('Booted', res['event_detail'])

            # Suspend the VM and check the event
            inst.vm_suspend('kimchi-vm1')
            time.sleep(5)
            res = json.loads(_get_event(str(_get_event_id())))
            self.assertEqual('kimchi-vm1', res['domain'])
            self.assertEqual('Suspended', res['event'])
            self.assertEqual('Paused', res['event_detail'])

            # Resume the VM and check the event
            inst.vm_resume('kimchi-vm1')
            time.sleep(5)
            res = json.loads(_get_event(str(_get_event_id())))
            self.assertEqual('kimchi-vm1', res['domain'])
            self.assertEqual('Resumed', res['event'])
            self.assertEqual('Unpaused', res['event_detail'])

            # PowerOff (hard stop) the VM and check the event
            inst.vm_poweroff('kimchi-vm1')
            time.sleep(5)
            res = json.loads(_get_event(str(_get_event_id())))
            self.assertEqual('kimchi-vm1', res['domain'])
            self.assertEqual('Stopped', res['event'])
            self.assertEqual('Destroyed', res['event_detail'])

            # Delete the VM and check the event
            inst.vm_delete('kimchi-vm1')
            time.sleep(5)
            res = json.loads(_get_event(str(_get_event_id())))
            self.assertEqual('kimchi-vm1', res['domain'])
            self.assertEqual('Undefined', res['event'])
            self.assertEqual('Removed', res['event_detail'])
