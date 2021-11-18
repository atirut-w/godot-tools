from gi.repository import Ide
from gi.repository import GObject
from gi.repository import Gio
from gi.repository import GLib

class GodotBuildSystemDiscovery(Ide.SimpleBuildSystemDiscovery):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.props.glob = '+(project\\.godot)'
        self.props.hint = 'godot-tools'
        self.props.priority = 1000

class GodotBuildSystem(Ide.Object, Ide.BuildSystem):
    project_file = GObject.Property(type=Gio.File)
    project_dir = None
    godot_exec = None

    def do_parent_set(self, parent):
        if self.project_file.query_file_type(0, None) == Gio.FileType.DIRECTORY:
            self.project_dir = self.project_file
        else:
            self.project_dir = self.project_file.get_parent()

    def do_get_id(self):
        return "godot"

    def do_get_display_name(self):
        return "Godot"

class GodotPipelineAddin(Ide.Object, Ide.PipelineAddin):
    def do_load(self, pipeline):
        context = pipeline.get_context()
        build_system = Ide.BuildSystem.from_context(context)

        if type(build_system) != GodotBuildSystem:
            return

        config = pipeline.get_config()
        runtime = config.get_runtime()

        godot = config.getenv("GODOT") or "godot"
        build_system.godot_exec = godot

    def _query(self, stage, pipeline, targets, cancellable):
        stage.set_completed(False)

class GodotRunTarget(Ide.Object, Ide.BuildTarget):
    def do_get_install_directory(self):
        return None

    def do_get_name(self):
        return 'Run project'

    def do_get_language(self):
        # Not meaningful, since we have an indirect process.
        return 'gdscript'

    def do_get_argv(self):
        context = self.get_context()
        build_system = Ide.BuildSystem.from_context(context)
        assert type(build_system) == GodotBuildSystem
        return [build_system.godot_exec, "--path", build_system.project_dir.get_path()]

    def do_get_priority(self):
        return 0

class MakeBuildTargetProvider(Ide.Object, Ide.BuildTargetProvider):
    def do_get_targets_async(self, cancellable, callback, data):
        task = Gio.Task.new(self, cancellable, callback)
        task.set_priority(GLib.PRIORITY_LOW)

        context = self.get_context()
        build_system = Ide.BuildSystem.from_context(context)

        if type(build_system) != GodotBuildSystem:
            task.return_error(GLib.Error('Not a Godot project',
                                         domain=GLib.quark_to_string(Gio.io_error_quark()),
                                         code=Gio.IOErrorEnum.NOT_SUPPORTED))
            return

        task.targets = [GodotRunTarget()]
        task.return_boolean(True)

    def do_get_targets_finish(self, result):
        if result.propagate_boolean():
            return result.targets


