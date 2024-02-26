# -*- coding: utf-8 -*-

#
# Copyright (c) 2022 Virtual Cable S.L.U.
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
import typing
import collections.abc
import logging


from uds.core import messaging

from ..fixtures import notifiers as notifiers_fixtures
from ..utils.test import UDSTestCase

if typing.TYPE_CHECKING:
    from uds import models


logger = logging.getLogger(__name__)


class EmailNotifierTest(UDSTestCase):
    """
    Test Email Notifier
    """

    def setUp(self) -> None:
        # Setup smtp server
        from aiosmtpd.controller import Controller
        from aiosmtpd.handlers import Debugging

        self.smtp_server = Controller(
            handler=Debugging(),
            hostname='localhost',
            port=1025,
        )
        self.smtp_server.start()  # type: ignore
        
    def tearDown(self) -> None:
        # Stop smtp debug server
        self.smtp_server.stop()

    def test_email_notifier(self) -> None:
        """
        Test email notifier
        """
        notifier = notifiers_fixtures.createEmailNotifier(
            host='localhost',
            port=self.smtp_server.port,
            enableHtml=False
        )

        notifier.get_instance().notify(
            'Group',
            'Identificator',
            messaging.LogLevel.CRITICAL,
            'Test message cañón',
        )

