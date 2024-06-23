import os
import maya.cmds as cmds
from database import SQLiteDB
from errors import DBException
from render_script import render_materials

### Constants

# This should point to the location of your asset Library which contains the relevant shaders directory.
# Replace Drive, directory and asset library with the appropriate folders for your system.
ASSET_LIBRARY_DIR = os.path.join("<DRIVE>", "<DIRECTORY>", "<ASSET LIBRARY>")

# Location of the Materials directory as well as the output directory. These must exist before using the tool.
MATERIALS_DIR = os.path.join(ASSET_LIBRARY_DIR, "Shaders")
OUTPUT_DIR = os.path.join(MATERIALS_DIR, ".mayaSwatches")

# This should have the appropriate name of the render camera of choice.
RENDER_CAM = "RenderCamShape"
# This should be the name of your geometry found in the attribute editor.
SHAPE_NAME = "shaderballShape"


### Directory Check


def check_directories():
    """Checks whether the directories are valid before continuing operation."""
    for directory in [ASSET_LIBRARY_DIR, MATERIALS_DIR, OUTPUT_DIR]:
        if not os.path.isdir(directory):
            print(f"Directory {directory} is invalid, cancelling operation.")
            return False
    return True


######################### Creation of UI ##########################


class NRJWindow(object):
    def __init__(self):
        self.window = "NRJ_Window"
        self.title = "Material Library Manager"
        self.size = (500, 250)
        self.task_list = None

        # Close and delete old window if already open
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window, window=True)

        # Create a new UI window
        self.window = cmds.window(
            self.window,
            title=self.title,
            widthHeight=self.size,
            sizeable=False,
            maximizeButton=False,
        )

        cmds.columnLayout(adjustableColumn=True)

        # Row for Title
        cmds.text(self.title, height=20)
        cmds.separator(height=20)

        # Row for buttons
        cmds.rowLayout(numberOfColumns=2)
        self.update_log_btn = cmds.button(
            label="Update Log", height=30, width=250, command=self.func_update_log_btn
        )

        self.render_btn = cmds.button(
            label="Render", height=30, width=250, command=self.func_render_btn
        )
        cmds.setParent("..")

        # Row for output box
        cmds.separator(height=20)
        self.text_scroll = cmds.scrollField(
            editable=False, wordWrap=True, width=400, height=140
        )
        cmds.separator(height=20)

        # Displays UI window
        cmds.showWindow()

    def func_update_log_btn(self, *args):
        """On button press, this function establishes a connection to the database and generates a task list."""
        self.clear_output()

        if not check_directories():
            self.update_output("Incorrect directories, cancelling operation.")
            return

        try:
            with SQLiteDB(MATERIALS_DIR) as db:
                db.update_log()
                self.task_list, task_message = db.generate_tasks(OUTPUT_DIR)
                self.update_output(task_message)
        except DBException as e:
            self.update_output(str(e))

    def func_render_btn(self, *args):
        """
        On button press, this triggers the render functions from the render_script file as well as
        updating and closing the database when finished.
        """
        self.clear_output()

        if not check_directories():
            self.update_output("Incorrect directories, cancelling operation.")
            return

        if not self.task_list:
            self.update_output(
                "No task list to render, cancelling operation. Please update the log."
            )
            return

        try:
            with SQLiteDB(MATERIALS_DIR) as db:
                render_output = render_materials(
                    self.task_list, MATERIALS_DIR, OUTPUT_DIR, RENDER_CAM, SHAPE_NAME
                )

                # receives return messages from the render output and updates the UI in Maya.
                for message in render_output[:3]:
                    if message:
                        self.update_output(message)

                update_db_error = db.update_db(render_output[3])
                if update_db_error:
                    self.update_output(update_db_error)

                cmds.select(SHAPE_NAME)
                cmds.hyperShade(assign="lambert1")
                self.task_list = None
        except DBException as e:
            self.update_output(str(e))

    def clear_output(self):
        cmds.scrollField(self.text_scroll, edit=True, clear=True)

    def update_output(self, return_message, *args):
        cmds.scrollField(self.text_scroll, edit=True, insertText=return_message + "\n")


def main():
    NRJWindow()


if __name__ == "__main__":
    main()
