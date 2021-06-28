#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
##  MIT License
##  
##  Copyright (c) 2021 Bash Club
##  
##  Permission is hereby granted, free of charge, to any person obtaining a copy
##  of this software and associated documentation files (the "Software"), to deal
##  in the Software without restriction, including without limitation the rights
##  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
##  copies of the Software, and to permit persons to whom the Software is
##  furnished to do so, subject to the following conditions:
##  
##  The above copyright notice and this permission notice shall be included in all
##  copies or substantial portions of the Software.
##  
##  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
##  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
##  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
##  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
##  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
##  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
##  SOFTWARE.

from cmk.gui.i18n import _
from cmk.gui.plugins.wato import (
    HostRulespec,
    IndividualOrStoredPassword,
    rulespec_registry,
)
from cmk.gui.valuespec import (
    Dictionary,
    Alternative,
    NetworkPort,
    Checkbox,
    TextAscii,
)

from cmk.gui.plugins.wato.datasource_programs import RulespecGroupDatasourceProgramsHardware

def _valuespec_special_agent_unifi_controller():
    return Dictionary(
        title = _('Unifi Controller via API'),
        help = _('This rule selects the Unifi API agent'),
        optional_keys=['site'],
        elements=[
            ('user',TextAscii(title = _('API Username.'),allow_empty = False,)),
            ('password',IndividualOrStoredPassword(title = _('API password'),allow_empty = False,)),
            ('site',TextAscii(title = _('Site Name'),allow_empty = False,default_value='default')), ## optional but not empty
            ('port',NetworkPort(title = _('Port'),default_value = 443)),
            ('ignore_cert', Checkbox(title=_("Ignore certificate validation"), default_value=False)),
            ('piggyback', 
                Alternative(
                    title = _('Receive piggyback data by'),
                    elements = [
                        FixedValue("name", title = _("Hostname")),
                        FixedValue("ip", title = _("IP")),
                        FixedValue("none", title = _("None")),
                    ],
                    default_value = "name"
                )
            )
        ]
    )

rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupDatasourceProgramsHardware,
        #IMPORTANT, name must follow special_agents:<name>, 
        #where filename of our special agent located in path local/share/check_mk/agents/special/ is  agent_<name>
        name='special_agents:unifi_controller',
        valuespec=_valuespec_special_agent_unifi_controller,
    ))

