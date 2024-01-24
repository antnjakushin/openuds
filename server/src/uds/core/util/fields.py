# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2023 Virtual Cable S.L.U.
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
import functools
import logging
import typing
import collections.abc

from django.utils.translation import gettext as _
from django.db.models import Q

from cryptography.x509 import load_pem_x509_certificate

from uds import models
from uds.core import types, ui

if typing.TYPE_CHECKING:
    from cryptography.x509 import Certificate

logger = logging.getLogger(__name__)

# ******************************************************
# Tunnel related common use fields and related functions
# ******************************************************


def _server_group_values(
    types_: collections.abc.Iterable[types.servers.ServerType], subtype: typing.Optional[str] = None
) -> list[types.ui.ChoiceItem]:
    fltr = models.ServerGroup.objects.filter(
        functools.reduce(lambda x, y: x | y, [Q(type=type_) for type_ in types_])
    )
    if subtype is not None:
        fltr = fltr.filter(subtype=subtype)

    return [
        ui.gui.choice_item(v.uuid, f'{v.name} {("("+ v.pretty_host + ")") if v.pretty_host else ""}')
        for v in fltr.all()
    ]


def _server_group_from_field(fld: ui.gui.ChoiceField) -> models.ServerGroup:
    try:
        return models.ServerGroup.objects.get(uuid=fld.value)
    except Exception:
        return models.ServerGroup()


# Tunnel server field
def tunnel_field() -> ui.gui.ChoiceField:
    """Returns a field to select a tunnel server"""
    return ui.gui.ChoiceField(
        label=_('Tunnel server'),
        order=1,
        tooltip=_('Tunnel server to use'),
        required=True,
        choices=functools.partial(_server_group_values, [types.servers.ServerType.TUNNEL]),
        tab=types.ui.Tab.TUNNEL,
        old_field_name='tunnel',
    )


def get_tunnel_from_field(fld: ui.gui.ChoiceField) -> models.ServerGroup:
    """Returns a tunnel server from a field"""
    return _server_group_from_field(fld)


# Server group field
def server_group_field(
    valid_types: typing.Optional[list[types.servers.ServerType]] = None,
    subtype: typing.Optional[str] = None,
    tab: typing.Optional[types.ui.Tab] = None,
) -> ui.gui.ChoiceField:
    """Returns a field to select a server group

    Args:
        type: Type of server group to select
        subktype: Subtype of server group to select (if any)

    Returns:
        A ChoiceField with the server group selection
    """
    valid_types = valid_types or [types.servers.ServerType.UNMANAGED]
    return ui.gui.ChoiceField(
        label=_('Server group'),
        order=2,
        tooltip=_('Server group to use'),
        required=True,
        choices=functools.partial(
            _server_group_values, valid_types, subtype
        ),  # So it gets evaluated at runtime
        tab=tab,
        old_field_name='serverGroup',
    )


def get_server_group_from_field(fld: ui.gui.ChoiceField) -> models.ServerGroup:
    """Returns a server group from a field

    Args:
        fld: Field to get server group from
    """
    return _server_group_from_field(fld)


# Ticket validity time field (for http related tunnels)
def tunnel_ticket_validity_field() -> ui.gui.NumericField:
    return ui.gui.NumericField(
        length=3,
        label=_('Ticket Validity'),
        default=60,
        order=90,
        tooltip=_(
            'Allowed time, in seconds, for HTML5 client to reload data from UDS Broker. The default value of 60 is recommended.'
        ),
        required=True,
        min_value=60,
        tab=types.ui.Tab.ADVANCED,
        old_field_name='ticketValidity',
    )


# Tunnel wait time (for uds client related tunnels)
def tunnel_wait_time_field(order: int = 2) -> ui.gui.NumericField:
    return ui.gui.NumericField(
        length=3,
        label=_('Tunnel wait time'),
        default=30,
        min_value=5,
        max_value=3600 * 24,
        order=order,
        tooltip=_('Maximum time, in seconds, to wait before disable new connections on client tunnel listener'),
        required=True,
        tab=types.ui.Tab.TUNNEL,
        old_field_name='tunnelWait',
    )


# Get certificates from field
def get_certificates_from_field(
    field: ui.gui.TextField, field_value: typing.Optional[str] = None
) -> list['Certificate']:
    # Get certificates in self.publicKey.value, encoded as PEM
    # Return a list of certificates in DER format
    value = (field_value or field.value).strip()
    if value == '':
        return []

    # Get certificates in PEM format
    pemCerts = value.split('-----END CERTIFICATE-----')
    # Remove empty strings
    pemCerts = [cert for cert in pemCerts if cert.strip() != '']
    # Add back the "-----END CERTIFICATE-----" part
    pemCerts = [cert + '-----END CERTIFICATE-----' for cert in pemCerts]

    # Convert to DER format
    certs: list['Certificate'] = []  # PublicKey...
    for pemCert in pemCerts:
        certs.append(load_pem_x509_certificate(pemCert.encode('ascii'), None))

    return certs


# Timeout
def timeout_field(
    default: int = 3,
    order: int = 90, tab: 'types.ui.Tab|str|None' = None, old_field_name: typing.Optional[str] = None
) -> ui.gui.NumericField:
    return ui.gui.NumericField(
        length=3,
        label=_('Timeout'),
        default=default,
        order=order,
        tooltip=_('Timeout in seconds for network connections'),
        required=True,
        min_value=1,
        tab=tab or types.ui.Tab.ADVANCED,
        old_field_name=old_field_name,
    )

# Ssl verification    
def verify_ssl_field(
    default: bool = True,
    order: int = 92, tab: 'types.ui.Tab|str|None' = None, old_field_name: typing.Optional[str] = None
) -> ui.gui.CheckBoxField:
        return ui.gui.CheckBoxField(
        label=_('Verify SSL'),
        default=default,
        order=order,
        tooltip=_(
            'If checked, SSL verification will be enforced. If not, SSL verification will be disabled'
        ),
        tab=tab or types.ui.Tab.ADVANCED,
        old_field_name=old_field_name,
    )
    

# Basename field
def basename_field(order: int = 32, tab: 'types.ui.Tab|str|None' = None) -> ui.gui.TextField:
    return ui.gui.TextField(
        label=_('Base Name'),
        order=order,
        tooltip=_('Base name for clones from this service'),
        tab=tab,
        required=True,
        old_field_name='baseName',
    )


# Length of name field
def lenname_field(
    order: int = 33, tab: 'types.ui.Tab|str|None' = None
) -> ui.gui.NumericField:
    return ui.gui.NumericField(
        length=1,
        label=_('Name Length'),
        default=3,
        order=order,
        tooltip=_('Size of numeric part for the names derived from this service'),
        tab=tab,
        required=True,
        old_field_name='lenName',
    )


# Max preparing services field
def max_preparing_services_field(
    order: int = 50, tab: typing.Optional[types.ui.Tab] = None
) -> ui.gui.NumericField:
    # Advanced tab
    return ui.gui.NumericField(
        length=3,
        label=_('Creation concurrency'),
        default=30,
        min_value=1,
        max_value=65536,
        order=order,
        tooltip=_('Maximum number of concurrently creating VMs'),
        required=True,
        tab=tab or types.ui.Tab.ADVANCED,
        old_field_name='maxPreparingServices',
    )


def max_removing_services_field(
    order: int = 51, tab: 'types.ui.Tab|str|None' = None
) -> ui.gui.NumericField:
    return ui.gui.NumericField(
        length=3,
        label=_('Removal concurrency'),
        default=15,
        min_value=1,
        max_value=65536,
        order=order,
        tooltip=_('Maximum number of concurrently removing VMs'),
        required=True,
        tab=tab or types.ui.Tab.ADVANCED,
        old_field_name='maxRemovingServices',
    )


def remove_duplicates_field(
    order: int = 102, tab: 'types.ui.Tab|str|None' = None
) -> ui.gui.CheckBoxField:
    return ui.gui.CheckBoxField(
        label=_('Remove found duplicates'),
        default=True,
        order=order,
        tooltip=_('If active, found duplicates vApps for this service will be removed'),
        tab=tab or types.ui.Tab.ADVANCED,
        old_field_name='removeDuplicates',
    )


def soft_shutdown_field(
    order: int = 103,
    tab: 'types.ui.Tab|str|None' = None,
    old_field_name: typing.Optional[str] = None,
) -> ui.gui.CheckBoxField:
    return ui.gui.CheckBoxField(
        label=_('Try SOFT Shutdown first'),
        default=False,
        order=order,
        tooltip=_(
            'If active, UDS will try to shutdown (soft) the machine using Nutanix ACPI. Will delay 30 seconds the power off of hanged machines.'
        ),
        tab=tab or types.ui.Tab.ADVANCED,
        old_field_name=old_field_name,
    )


def keep_on_access_error_field(
    order: int = 104,
    tab: 'types.ui.Tab|str|None' = None,
    old_field_name: typing.Optional[str] = None,
) -> ui.gui.CheckBoxField:
    return ui.gui.CheckBoxField(
        label=_('Keep on error'),
        value=False,
        order=order,
        tooltip=_('If active, access errors found on machine will not be considered errors.'),
        tab=tab or types.ui.Tab.ADVANCED,
        old_field_name=old_field_name,
    )


def macs_range_field(
    default: str,
    order: int = 91,
    tab: 'types.ui.Tab|str|None' = None,
    readonly: bool = False,
) -> ui.gui.TextField:
    return ui.gui.TextField(
        length=36,
        label=_('Macs range'),
        default=default,
        order=order,
        readonly=readonly,
        tooltip=_('Range of valid macs for created machines. Must be in the range {default}').format(
            default=default
        ),
        required=True,
        tab=tab or types.ui.Tab.ADVANCED,
        old_field_name='macsRange',
    )
