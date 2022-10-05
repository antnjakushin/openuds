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

from uds.models import Log, getSqlDatetime
from uds.core.util.log import (
    REST,
    OWNER_TYPE_REST,
    DEBUG,
    INFO,
    WARNING,
    ERROR,
    CRITICAL,
    # These are legacy support until full removal
    WARN,
    FATAL,
)


if typing.TYPE_CHECKING:
    from .handlers import Handler


def log_operation(handler: typing.Optional['Handler'], response_code: int, level: int = INFO):
    """
    Logs a request
    """
    if not handler:
        return  # Nothing to log
    username = handler._request.user.pretty_name if handler._request.user else 'Unknown'
    # Global log is used without owner nor type
    Log.objects.create(
        owner_id=0,
        owner_type=OWNER_TYPE_REST,
        created=getSqlDatetime(),
        level=level,
        source=REST,
        data=f'{username}: [{handler._request.method}/{response_code}] {handler._request.path}'[
            :255
        ],
    )
