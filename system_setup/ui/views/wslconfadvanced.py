""" WSLConfigurationAdvanced View

WSLConfigurationAdvanced provides user with options with additional settings
for advanced configuration.

"""
import re

from urwid import (
    connect_signal,
)

from subiquitycore.ui.form import (
    Form,
    BooleanField,
    ChoiceField,
    simple_field,
    WantsToKnowFormField
)
from subiquitycore.ui.interactive import StringEditor
from subiquitycore.ui.utils import screen
from subiquitycore.view import BaseView
from subiquity.common.types import WSLConfigurationAdvanced


class MountEditor(StringEditor, WantsToKnowFormField):
    def keypress(self, size, key):
        ''' restrict what chars we allow for mountpoints '''

        mountpoint = r'[a-zA-Z0-9_/\.\-]'
        if re.match(mountpoint, key) is None:
            return False

        return super().keypress(size, key)


MountField = simple_field(MountEditor)
StringField = simple_field(StringEditor)


class WSLConfigurationAdvancedForm(Form):
    def __init__(self, initial):
        super().__init__(initial=initial)

    automount_enabled = \
        BooleanField(_("Enable Auto-Mount"),
                     help=_("Whether the Auto-Mount freature is enabled. "
                            "This feature allows you to mount Windows drive"
                            " in WSL."))
    automount_mountfstab = \
        BooleanField(_("Mount `/etc/fstab`"),
                     help=_("Whether `/etc/fstab` will be mounted. The "
                            "configuration file `/etc/fstab` contains "
                            "the necessary information to automate the"
                            " process of mounting partitions. "))
    interop_enabled = \
        BooleanField(_("Enable Interop"),
                     help=_("Whether the interoperability is enabled"))
    interop_appendwindowspath = \
        BooleanField(_("Append Windows Path"),
                     help=_("Whether Windows Path will be append in the"
                            " PATH environment variable in WSL."))
    gui_theme = \
        ChoiceField(_("GUI Theme"),
                    help=_("This option changes the Ubuntu theme."),
                    choices=["default", "light", "dark"])
    gui_followwintheme = \
        BooleanField(_("Follow Windows Theme"),
                     help=_("This option manages whether the Ubuntu theme"
                            " follows the Windows theme; that is, when "
                            "Windows uses dark theme, Ubuntu also uses dark"
                            " theme. Requires WSL interoperability enabled. "))
    interop_guiintegration = \
        BooleanField(_("Legacy GUI Integration"),
                     help=_("This option enables the Legacy GUI Integration "
                     "on Windows 10. Requires a Third-party X Server."))
    interop_audiointegration = \
        BooleanField(_("Legacy Audio Integration"),
                     help=_("This option enables the Legacy Audio Integration "
                            "on Windows 10. Requires PulseAudio for Windows "
                            "Installed."))
    interop_advancedipdetection = \
        BooleanField(_("Advanced IP Detection"),
                     help=_("This option enables advanced detection of IP by "
                            "Windows IPv4 Address which is more reliable to "
                            "use with WSL2. Requires WSL interoperability "
                            "enabled."))
    motd_wslnewsenabled = \
        BooleanField(_("Enable WSL News"),
                     help=_("This option allows you to control your MOTD News."
                            " Toggling it on allows you to see the MOTD."))


class WSLConfigurationAdvancedView(BaseView):
    title = _("WSL Configuration - Advanced options")
    excerpt = _("In this page, you can configure Ubuntu WSL "
                "advanced options your needs. \n")

    def __init__(self, controller, configuration_data):
        self.controller = controller

        initial = {
            'interop_enabled':
                configuration_data.interop_enabled,
            'interop_appendwindowspath':
                configuration_data.interop_appendwindowspath,
            'gui_theme':
                configuration_data.gui_theme,
            'gui_followwintheme':
                configuration_data.gui_followwintheme,
            'interop_guiintegration':
                configuration_data.interop_guiintegration,
            'interop_audiointegration':
                configuration_data.interop_audiointegration,
            'interop_advancedipdetection':
                configuration_data.interop_advancedipdetection,
            'motd_wslnewsenabled':
                configuration_data.motd_wslnewsenabled,
            'automount_enabled':
                configuration_data.automount_enabled,
            'automount_mountfstab':
                configuration_data.automount_mountfstab,
        }
        self.form = WSLConfigurationAdvancedForm(initial=initial)

        connect_signal(self.form, 'submit', self.done)
        super().__init__(
            screen(
                self.form.as_rows(),
                [self.form.done_btn],
                focus_buttons=True,
                excerpt=self.excerpt,
            )
        )

    def done(self, result):
        self.controller.done(WSLConfigurationAdvanced(
            interop_enabled=self.form
            .interop_enabled.value,
            interop_appendwindowspath=self.form
            .interop_appendwindowspath.value,
            gui_theme=self.form
            .gui_theme.value,
            gui_followwintheme=self.form
            .gui_followwintheme.value,
            interop_guiintegration=self.form
            .interop_guiintegration.value,
            interop_audiointegration=self.form
            .interop_audiointegration.value,
            interop_advancedipdetection=self.form
            .interop_advancedipdetection.value,
            motd_wslnewsenabled=self.form
            .motd_wslnewsenabled.value,
            automount_enabled=self.form
            .automount_enabled.value,
            automount_mountfstab=self.form
            .automount_mountfstab.value,
            ))
