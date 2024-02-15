#
# Copyright (c) 2012-2022 Virtual Cable S.L.U.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#    * Neither the name of Virtual Cable S.L.U. nor the names of its contributors
#      may be used to endorse or promote products derived from this software
#      without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Author: Adolfo Gómez, dkmaster at dkmon dot com
"""
import logging
import typing

from django.utils.translation import gettext_noop as _, gettext
from uds.core import services, types, consts, exceptions
from uds.core.services.specializations.fixed_machine.fixed_service import FixedService
from uds.core.services.specializations.fixed_machine.fixed_userservice import FixedUserService
from uds.core.ui import gui
from uds.core.util import validators, log
from uds.core.util.decorators import cached
from uds.core.workers import initialize

from . import helpers
from .deployment_fixed import XenFixedUserService

# Not imported at runtime, just for type checking
if typing.TYPE_CHECKING:
    from uds.core.module import Module
    from uds import models

    from .provider import XenProvider

logger = logging.getLogger(__name__)


class XenFixedService(FixedService):  # pylint: disable=too-many-public-methods
    """
    Represents a Proxmox service based on fixed machines.
    This service requires the qemu agent to be installed on the machines.
    """

    type_name = _('Proxmox Fixed Machines')
    type_type = 'ProxmoxFixedService'
    type_description = _('Proxmox Services based on fixed machines. Needs qemu agent installed on machines.')
    icon_file = 'service.png'

    can_reset = True

    # : Types of publications (preparated data for deploys)
    # : In our case, we do no need a publication, so this is None
    publication_type = None
    # : Types of deploys (services in cache and/or assigned to users)
    user_service_type = XenFixedUserService

    allowed_protocols = types.transports.Protocol.generic_vdi(types.transports.Protocol.SPICE)
    services_type_provided = types.services.ServiceType.VDI

    # Gui
    token = FixedService.token

    folder = gui.ChoiceField(
        label=_("Folder"),
        readonly=False,
        order=20,
        fills={
            'callback_name': 'xmFillMachinesFromFolder',
            'function': helpers.get_machines,
            'parameters': ['prov_uuid', 'folder'],
        },
        tooltip=_('Folder containing base machines'),
        required=True,
        tab=_('Machines'),
        old_field_name='resourcePool',
    )
    machines = FixedService.machines
    use_snapshots = FixedService.use_snapshots

    prov_uuid = gui.HiddenField(value=None)

    def initialize(self, values: 'Module.ValuesType') -> None:
        """
        Loads the assigned machines from storage
        """
        if values:
            if not self.machines.value:
                raise exceptions.ui.ValidationError(gettext('We need at least a machine'))

            self.storage.put_pickle('userservices_limit', len(self.machines.as_list()))

            # Remove machines not in values from "assigned" set
            self._save_assigned_machines(self._get_assigned_machines() & set(self.machines.as_list()))
            self.token.value = self.token.value.strip()
        self.userservices_limit = self.storage.get_unpickle('userservices_limit')

    def init_gui(self) -> None:
        # Here we have to use "default values", cause values aren't used at form initialization
        # This is that value is always '', so if we want to change something, we have to do it
        # at defValue
        self.prov_uuid.value = self.parent().get_uuid()

        self.folder.set_choices([gui.choice_item(folder, folder) for folder in self.parent().list_folders()])

    def parent(self) -> 'XenProvider':
        return typing.cast('XenProvider', super().parent())

    def get_machine_power_state(self, machine_id: str) -> str:
        """
        Invokes getMachineState from parent provider

        Args:
            machineId: If of the machine to get state

        Returns:
            one of this values:
        """
        return self.parent().get_machine_power_state(machine_id)

    def start_machine(self, machine_id: str) -> typing.Optional[str]:
        """
        Tries to start a machine. No check is done, it is simply requested to Xen.

        This start also "resume" suspended/paused machines

        Args:
            machineId: Id of the machine

        Returns:
        """
        return self.parent().start_machine(machine_id)

    def stop_machine(self, machine_id: str) -> typing.Optional[str]:
        """
        Tries to stop a machine. No check is done, it is simply requested to Xen

        Args:
            machineId: Id of the machine

        Returns:
        """
        return self.parent().stop_machine(machine_id)

    def reset_machine(self, machine_id: str) -> typing.Optional[str]:
        """
        Tries to stop a machine. No check is done, it is simply requested to Xen

        Args:
            machineId: Id of the machine

        Returns:
        """
        return self.parent().reset_machine(machine_id)

    def shutdown_machine(self, vm_id: str) -> typing.Optional[str]:
        return self.parent().shutdown_machine(vm_id)

    def check_task_finished(self, task: str) -> tuple[bool, str]:
        return self.parent().check_task_finished(task)

    @cached('reachable', consts.cache.SHORT_CACHE_TIMEOUT)
    def is_avaliable(self) -> bool:
        return self.parent().is_available()

    def enumerate_assignables(self) -> list[tuple[str, str]]:
        # Obtain machines names and ids for asignables
        vms: dict[int, str] = {}

        assigned_vms = self._get_assigned_machines()
        return [(k, vms.get(int(k), 'Unknown!')) for k in self.machines.as_list() if int(k) not in assigned_vms]

    def assign_from_assignables(
        self, assignable_id: str, user: 'models.User', user_deployment: 'services.UserService'
    ) -> str:
        userservice_instance = typing.cast(XenFixedUserService, user_deployment)
        assigned_vms = self._get_assigned_machines()
        if assignable_id not in assigned_vms:
            assigned_vms.add(assignable_id)
            self._save_assigned_machines(assigned_vms)
            return userservice_instance.assign(assignable_id)

        return userservice_instance.error('VM not available!')

    def process_snapshot(self, remove: bool, userservice_instace: FixedUserService) -> str:
        userservice_instace = typing.cast(XenFixedUserService, userservice_instace)
        if self.use_snapshots.as_bool():
            vmid = userservice_instace._vmid

            snapshots = [i['id'] for i in self.parent().list_snapshots(vmid)]
            snapshot = snapshots[0] if snapshots else None

            if remove and snapshot:
                try:
                    userservice_instace._task = self.parent().restore_snapshot(snapshot['id'])
                except Exception as e:
                    self.do_log(log.LogLevel.WARNING, 'Could not restore SNAPSHOT for this VM. ({})'.format(e))

            else:
                logger.debug('Using snapshots')
                # If no snapshot exists for this vm, try to create one for it on background
                # Lauch an snapshot. We will not wait for it to finish, but instead let it run "as is"
                try:
                    if not snapshot:  # No snapshot, try to create one
                        logger.debug('Not current snapshot')
                        # We don't need the snapshot nor the task, will simply restore to newer snapshot on remove
                        self.parent().create_snapshot(
                            vmid,
                            name='UDS Snapshot',
                        )
                except Exception as e:
                    self.do_log(log.LogLevel.WARNING, 'Could not create SNAPSHOT for this VM. ({})'.format(e))

        return types.states.State.RUNNING

    def get_and_assign_machine(self) -> str:
        found_vmid: typing.Optional[str] = None
        try:
            assigned_vms = self._get_assigned_machines()
            for k in self.machines.as_list():
                checking_vmid = k
                if found_vmid not in assigned_vms:  # Not assigned
                    # Check that the machine exists...
                    try:
                        vm_name = self.parent().get_machine_name(checking_vmid)
                        found_vmid = checking_vmid
                        break
                    except Exception:  # Notifies on log, but skipt it
                        self.parent().do_log(
                            log.LogLevel.WARNING, 'Machine {} not accesible'.format(found_vmid)
                        )
                        logger.warning(
                            'The service has machines that cannot be checked on proxmox (connection error or machine has been deleted): %s',
                            found_vmid,
                        )

            if found_vmid:
                assigned_vms.add(str(found_vmid))
                self._save_assigned_machines(assigned_vms)
        except Exception:  #
            raise Exception('No machine available')

        if not found_vmid:
            raise Exception('All machines from list already assigned.')

        return str(found_vmid)

    def get_first_network_mac(self, vmid: str) -> str:
        return self.parent().get_first_mac(vmid)

    def get_guest_ip_address(self, vmid: str) -> str:
        return self.parent().get_first_ip(vmid)

    def get_machine_name(self, vmid: str) -> str:
        return self.parent().get_machine_name(vmid)

    def remove_and_free_machine(self, vmid: str) -> str:
        try:
            self._save_assigned_machines(self._get_assigned_machines() - {str(vmid)})  # Remove from assigned
            return types.states.State.FINISHED
        except Exception as e:
            logger.warning('Cound not save assigned machines on fixed pool: %s', e)
            raise