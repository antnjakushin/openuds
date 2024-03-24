# -*- coding: utf-8 -*-

#
# Copyright (c) 2024 Virtual Cable S.L.U.
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
Authot: Adolfo Gómez, dkmaster at dkmon dot com
"""
import dataclasses
import typing
from unittest import mock

from uds import models
from uds.core import types
from uds.core.services.generics.fixed import (
    userservice,
)
from ....utils.test import UDSTestCase
from . import fixtures


@dataclasses.dataclass
class FixedServiceIterationInfo:
    queue: list[userservice.Operation]
    service_calls: list[mock._Call] = dataclasses.field(default_factory=list)
    user_service_calls: list[mock._Call] = dataclasses.field(default_factory=list)
    state: str = types.states.TaskState.RUNNING

    def __mul__(self, other: int) -> list['FixedServiceIterationInfo']:
        return [self] * other


EXPECTED_DEPLOY_ITERATIONS_INFO: typing.Final[list[FixedServiceIterationInfo]] = [
    # Initial state for queue
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.CREATE,
            userservice.Operation.SNAPSHOT_CREATE,
            userservice.Operation.PROCESS_TOKEN,
            userservice.Operation.START,
            userservice.Operation.FINISH,
        ],
        service_calls=[
            mock.call.get_and_assign_machine(),
            mock.call.get_first_network_mac('assigned'),
            mock.call.get_machine_name('assigned'),
        ],
    ),
    # Machine has no snapshot, and it's running, try to stop
    # (this is what our testing example does, but maybe it's not the best approach for all services)
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.NOP,
            userservice.Operation.STOP,
            userservice.Operation.SNAPSHOT_CREATE,
            userservice.Operation.PROCESS_TOKEN,
            userservice.Operation.START,
            userservice.Operation.FINISH,
        ],
        service_calls=[
            mock.call.process_snapshot(False, mock.ANY),
        ],
    ),
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.STOP,
            userservice.Operation.SNAPSHOT_CREATE,
            userservice.Operation.PROCESS_TOKEN,
            userservice.Operation.START,
            userservice.Operation.FINISH,
        ],
        user_service_calls=[mock.call._stop_machine()],
    ),
    # The current operation is snapshot, so check previous operation (Finished) and then process snapshot
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.SNAPSHOT_CREATE,
            userservice.Operation.PROCESS_TOKEN,
            userservice.Operation.START,
            userservice.Operation.FINISH,
        ],
        service_calls=[
            mock.call.process_snapshot(False, mock.ANY),
        ],
        user_service_calls=[mock.call._stop_checker()],
    ),
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.PROCESS_TOKEN,
            userservice.Operation.START,
            userservice.Operation.FINISH,
        ],
        user_service_calls=[mock.call.db_obj()],
    ),
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.START,
            userservice.Operation.FINISH,
        ],
        user_service_calls=[mock.call._start_machine()],
    ),
    # When in queue is only finish, it's the last iteration
    # (or if queue is empty, but that's not the case here)
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.FINISH,
        ],
        user_service_calls=[mock.call._start_checker()],
        state=types.states.TaskState.FINISHED,
    ),
]

EXPECTED_REMOVAL_ITERATIONS_INFO: typing.Final[list[FixedServiceIterationInfo]] = [
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.REMOVE,
            userservice.Operation.SNAPSHOT_RECOVER,
            userservice.Operation.FINISH,
        ],
        service_calls=[mock.call.remove_and_free_machine('assigned')],
    ),
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.SNAPSHOT_RECOVER,
            userservice.Operation.FINISH,
        ],
        service_calls=[mock.call.process_snapshot(True, mock.ANY)],
    ),
    FixedServiceIterationInfo(
        queue=[
            userservice.Operation.FINISH,
        ],
        state=types.states.TaskState.FINISHED,
    ),
]


class FixedServiceTest(UDSTestCase):
    def create_elements(
        self,
    ) -> tuple['fixtures.FixedTestingProvider', 'fixtures.FixedTestingService', 'fixtures.FixedTestingUserService']:
        environment = self.create_environment()
        prov = fixtures.FixedTestingProvider(environment=environment)
        service = fixtures.FixedTestingService(environment=environment, provider=prov)
        user_service = fixtures.FixedTestingUserService(environment=environment, service=service)

        return prov, service, user_service

    def check_iterations(
        self,
        service: 'fixtures.FixedTestingService',
        userservice: 'fixtures.FixedTestingUserService',
        iterations: list[FixedServiceIterationInfo],
        removal: bool,
    ) -> None:
        first: bool = True

        for iteration in iterations:
            # Clear mocks
            service.mock.reset_mock()
            userservice.mock.reset_mock()

            if first:  # First iteration is call for deploy
                if not removal:
                    state = userservice.deploy_for_user(models.User())
                else:
                    state = userservice.destroy()
                first = False
            else:
                state = userservice.check_state()
            self.assertEqual(state, iteration.state, f'Iteration {iteration} {state}')
            self.assertEqual(
                userservice._queue,
                iteration.queue,
                f'Iteration {iteration} {userservice._queue} {iteration.queue}',
            )
            self.assertEqual(
                service.mock.mock_calls,
                iteration.service_calls,
                f'Iteration {iteration} {userservice._queue}',
            )
            self.assertEqual(
                userservice.mock.mock_calls,
                iteration.user_service_calls,
                f'Iteration {iteration} {userservice._queue}',
            )

    def deploy_service(
        self, service: 'fixtures.FixedTestingService', userservice: 'fixtures.FixedTestingUserService', max_iterations: int = 100
    ) -> None:
        if userservice.deploy_for_user(models.User()) != types.states.TaskState.FINISHED:
            while userservice.check_state() != types.states.TaskState.FINISHED and max_iterations > 0:
                max_iterations -= 1

        # Clear mocks
        service.mock.reset_mock()
        userservice.mock.reset_mock()

    def test_service_deploy(self) -> None:
        _prov, service, userservice = self.create_elements()
        self.check_iterations(service, userservice, EXPECTED_DEPLOY_ITERATIONS_INFO, removal=False)
        
    def test_service_deploy_no_machine(self) -> None:
        _prov, service, userservice = self.create_elements()
        service.available_machines_number = 2
        self.deploy_service(service, userservice)  # Should be deployed without issues
        self.deploy_service(service, userservice)  # Should be deployed without issues, 2nd time
        # And now, should fail to deploy again
        self.assertRaises(Exception, self.deploy_service, service, userservice)

    def test_service_removal(self) -> None:
        _prov, service, userservice = self.create_elements()

        # Ensure fully deployed state for userservice
        self.deploy_service(service, userservice)

        # Userservice is in deployed state, so we can remove it
        self.check_iterations(service, userservice, EXPECTED_REMOVAL_ITERATIONS_INFO, removal=True)


