# Material Library Manager
#### Video Demo: 
https://youtu.be/8jNkHfn2C8U

#### Description:

`Material Library Manager` is a tool created for Maya using Python. It is designed to render out thumbnails of materials in a directory, _such as a material asset library_, so that artists can preview a material when viewing it in the content browser.
<p align="center"> <img src="https://github.com/nrjones-dev/material_library_manager/assets/115369332/caaf6828-c782-4bb0-922c-78811fe01fc6" /> </p>

# Contents

* [Why?](#why)
* [How?](#how)
  * [main.py](#mainpy)
  * [database.py](#databasepy)
  * [render_script.py](#renderscriptpy)
  * [errors.py](#errorspy)
* [Installation](#installation)
* [Usage](#usage)
* [Future Improvements](#future-improvements)


### Why?

I wanted to create a tool that allows you to:

+ Create previewable images and thumbnails of multiple material files at once, in order to view them inside Maya's Content Browser.
+ Keep track of when files were last modified and when files were last rendered in a database.
+ Run a script within Maya to render out any new or updated files from this database.
+ Run the tool without any knowledge of python or scripting in general, i.e using a simple user interface.


### How?

The functionality of this tool is broken down into 4 scripts, each focusing on a specific element.

#### Main.py

This script is responsible for setting the core directories, the name of the geometry that materials should be assigned to as well as creating the UI for the user.

When the script shortcut is activated on Maya's shelf, the main function within this script will be triggered, creating the UI seen at the top of this page.
<p> <img src="https://github.com/nrjones-dev/material_library_manager/assets/115369332/df40db26-16bb-4eaa-a8bf-b6ca53838a13"> </p>

This UI is set at a preset resolution and is not resizeable. It will also be destroyed and re-created if the user attempts to open multiple versions. Inside the UI is a title, two buttons and an output window. 

The `Update Log` button will firstly clear any existing output messages, check that the directories still exist and are correct and then call a function inside of the `database.py` script called `update_log()`. Once this is done and has returned a successful result, the `generate_tasks()` function within the `database.py` script will be called. The final result will then be displayed on the output console.

The `Render` button will also clear any existing messages, check directories as well as database connections and then check if a `task_list` exists. If it doesn't, a message will be returned. If a `task_list` is found then the `render_materials()` function is called within `render_script.py`. Once this has finished, messages will be returned to the user and the database will be updated with the returned result. The database will then be closed and the geometry assigned a default material once again. Finally the `task_list` will be dropped so that any further accidental button clicks on 'render' will not be activated.

#### Database.py

This script's main focus is a class called `SQliteDB`. It is responsible for methods relating to the sqlite3 database, acts as a context manager and automatically establishes a connection with the database when accessed and closes the connection when exited. It also creates a materials table if one does not already exist.

+ `Update_log()` then attempts to trigger `insert_new_materials_db()` and `delete_from_db()`. If any of these return an exception error as part of their return, the message will be returned to main. Otherwise the database connection and cursor (db) will be returned to main.

+ `create_table()` creates a table if it doesn't exist called materials, this is where all the material information is stored such as the id, material filename, date modified and date rendered. This method is called upon class initiation.  

+ `insert_new_materials_db()` creates a list of existing materials in the database and compare it against the list of files within the material directory that end with ".mb". This isolates the material files within the shaders directory and adds them to the database if they don't already exist. If the date modified timestamp in the file properties is more recent than the date modified in the database, then the date_modified is updated with the latest data.

+ `delete_from_db()` deletes any materials in the database that are no longer found within the shaders directory. 

+ `generate_tasks()` generates a list of materials that require rendering within maya and passes it back to the main function in order to display it in the UI and be fed into the `renderscript`. While doing so, it also triggers `check_swatches()` and combines the two sets into a single list, removing any duplicates.

+ `check_swatches()` generates a list of materials that may or may not require rendering based upon date modified, but are lacking a relevant ".SWATCH" file and therefore have no image preview available. This list is returned to `generate_tasks()`.

+ `update_db()` assigns the current unix time to a variable called `date_rendered` and updates all materials in the database with this time, based on a `rendered_list` that is passed into the function from main. 

+ `close_db()` closes the cursor (db) and connection to the database. This is called automatically when the class is exited out of in main.

#### Renderscript.py

This script is responsible for importing materials into maya, rendering them and saving the outputed images.

+ `import_mat()` imports the current material from the loop in `render_materials()` into the Maya scene and assigns them to the geometry set in the constant variable in `main.py`.

+ `render_with_arnold()` sets the render engine to Arnold within Maya and sets the output_path of rendered images defined in `render_materials()`.
  
+ `render_materials()` loops through each material in the `task_list` passed in from `main.py`, assigns a `material_path`, extracts a `shader_name` and then if the file exists calls `import_mat()`, assigns the output_path and calls `render_with_arnold()`. At the end of the loop the material is appended to the `rendered_list` inside this function. If the file doesn't exist, the material is appended to `missed_files`. Once all files have been looped through, the names of all materials and amount of materials rendered are returned to the UI in main. If there are missed files, these are also returned and displayed to the user.

### Installation
---
**To install, please follow the steps below:**

* From the `scripts` directory, copy `database.py`, `main.py` and `renderscript.py` to the scripts folder in the relevant version of Maya. This is typically found at `Users\[USERNAME]\Documents\maya\2022\scripts`.
*  From the `assets` directory, copy `MLM_Icon.png` to the prefs/icons folder within the same directory. This is typically found at `Users\[USERNAME]\Documents\maya\2022\prefs\icons`.
*  inside of `main.py`:
   * Set the correct directory in `ASSET_LIBRARY_DIR`. For example:
         <p>```ASSET_LIBRARY_DIR = os.path.join("C:/", "Users", "[USERNAME]", "Documents", "asset_library")```</p>
   * If they don't already exist, create a directory inside of this called **'Shaders'** and another directory inside of Shaders called **'.mayaSwatches'**.
   * Set the correct name for `RENDER_CAM` based upon the camera in your Maya scene.
   * Set the correct name for `SHAPE_NAME` based upon the geometry you wish the materials to be applied to.
* Open **Maya** and then the **Maya Script Editor**. Select **Python** as a language and write:
```
import main as MLM
MLM.main()
```
* Highlight this text and drag it to a **Maya Shelf** of your choice. Select **Python** once more. Now you can right click the button this creates and under **Shelves** assign the `MLM_icon.png`.
* The script should now be fully functional and run when this button is clicked.

### Usage

To use this tool, you must first export materials that will be used in **Maya's Content Browser**.
* In **Maya's Hypershade**, select a material node and name it appropriately, such as `aiGrass`.
* Click on **File** with the material still selected and select **Export Selected Network**.
* Navigate to the correct directory set in the installation instructions for **Shaders** and export the material with the same name as before `aiGrass` and save the file as **.mb**.
* Now open the render scene you have prepared and run the `Material Library Manager` through the button created earlier on the shelf.
* You may now click `Update Log` and then `Render`.
* If done correctly, the tool should create a `materials.db` file in the same directory and render out a swatch file for the material.
  * While it isn't required, this tool is designed to be used for batches of materials at a time and will be more efficient to do so.

### Future Improvements
---
There are some improvements I would like to implement on this tool in the future if it continues to be useful, these are:

* Allow the user to set default directories in the script, but not require it - allowing this to be done through the user interface.
* Removal of Swatch files when materials are removed from the database.
* Implement PySide or PyQt to keep with industry standards of UI inside Maya.
