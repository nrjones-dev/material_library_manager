import os

import maya.cmds as cmds


def import_mat(material_path, shader_name, shape_name):
    """Imports and assigns materials to shaderball inside maya scene"""
    cmds.file(material_path, i=True)
    cmds.select(shape_name)
    cmds.hyperShade(assign=shader_name)


def render_with_arnold(output_path, render_cam):
    """Render the scene using Arnold Renderer"""
    cmds.setAttr("defaultRenderGlobals.currentRenderer", "arnold", type="string")
    cmds.setAttr("defaultRenderGlobals.imageFilePrefix", output_path, type="string")
    cmds.arnoldRender(camera=render_cam)


def render_materials(task_list, materials_dir, output_dir, render_cam, shape_name):
    """Render the materials in the task list using Maya and Arnold renderer."""
    rendered_list = []
    missed_files = []

    for material in task_list:
        material_path = os.path.join(materials_dir, material)
        shader_name = os.path.splitext(material)[0]

        if os.path.isfile(material_path):
            import_mat(material_path, shader_name, shape_name)
            output_path = os.path.join(output_dir, material + ".SWATCH")
            render_with_arnold(output_path, render_cam)
            rendered_list.append(material)
        else:
            missed_files.append(material)
            print(f"{material} doesn't exist, check directory.")

    rendered_statement = f"The following materials have been rendered and saved to the asset library: {', '.join(rendered_list)}."
    number_tasks = f"This is {len(rendered_list)}/{len(task_list)} tasks."

    if missed_files:
        missed_files_statement = (
            f"The following files failed: {', '.join(missed_files)}."
        )

    else:
        missed_files_statement = None

    return [rendered_statement, number_tasks, missed_files_statement, rendered_list]
