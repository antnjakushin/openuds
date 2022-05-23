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
#    * Neither the name of Virtual Cable S.L. nor the names of its contributors
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
.. moduleauthor:: Adolfo Gómez, dkmaster at dkmon dot com
"""
import time
import logging
import typing

from uds.core.managers.task import BaseThread

from uds.models import Notifier, Notification
from .provider import Notifier as NotificationProviderModule

logger = logging.getLogger(__name__)

WAIT_TIME = 8  # seconds


class MessageProcessorThread(BaseThread):
    keepRunning: bool = True

    def __init__(self):
        super().__init__()
        self.setName('MessageProcessorThread')

    def run(self):
        # Load providers at beginning
        providers: typing.List[typing.Tuple[int, NotificationProviderModule]] = [
            (p.level, p.getInstance()) for p in Notifier.objects.all()
        ]

        while self.keepRunning:
            # Locate all notifications from "persistent" and try to process them
            # In no notification can be fully resolved, it will be kept in the database
            for n in Notification.getPersistentQuerySet().all():
                # Try to insert into Main DB
                notify = (
                    not n.processed
                )  # If it was already processed, the only thing left is to add to maind DB and remove it from persistent
                pk = n.pk
                n.processed = True
                try:
                    n.pk = None
                    n.save(using='default')
                    # Delete from Persistent DB, first restore PK
                    n.pk = pk
                    Notification.deletePersistent(n)
                    logger.debug('Saved notification %s to main DB', n)
                except Exception:
                    # try notificators, but keep on db with error
                    # Restore pk, and save locally so we can try again
                    n.pk = pk
                    Notification.savePersistent(n)
                    logger.warning(
                        'Could not save notification %s to main DB, trying notificators',
                        n,
                    )

                if notify:
                    for p in (i[1] for i in providers if i[0] >= n.level):
                        # if we are asked to stop, we don't try to send anymore
                        if not self.keepRunning:
                            break
                        p.notify(n.group, n.identificator, n.level, n.message)

            for a in range(WAIT_TIME):
                if not self.keepRunning:
                    break
                time.sleep(1)

    def notifyTermination(self):
        self.keepRunning = False