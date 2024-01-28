# Light-field renderer Blender Plugin

A Light field renderer using Blender's Python API. It was created for the research project "BAMBI" at the University of Applied Sciences Upper Austria.

![Example_Image](https://github.com/Richi4590/BambiLFVisualizer/assets/92519599/96bb7251-a11a-4ee7-91c9-615f2299302d)
*Figure: A screenshot of a recording at the parking area of the University of Applied Sciences Upper Austria.*

## Features
- Loading a light-field recording and viewing or rendering it inside of Blender.
- Previewing the number of images to be used for creating a merged image
- Specifying the focus (projection distance) of the cameras
- Specifying a range of different settings such as:
    - Selecting a different rendering camera
    - Setting the X and Y resolution of the final rendered image/video
    - Specifying a different rendering path, a DEM file or JSON file
    - If the rendered range of images should be available individually or being overwritten
 
### Dependencies

* This plugin was developed using Blender version 4.0
* Windows 10/11

### Getting started to develop
* Recommended Editor of choice: Visual Studio Code with the following extensions:
  - Python
  - Blender Development
  - Task Explorer
  - Optionally: Blender Python Code Templates

- Open the Addon-Folder with Visual Studio Code
- Press CTRL + SHIFT + P to open up the command window
- Type in "Blender: Start"
- Select the Blender Version you want to run the Add-on with
- Blender should open after some time
- To make changes to the code applicable, go to the command window again
- Enter "Blender: Reload Addons" (mapping this command as a Shortcut is recommended)

* To install and test the add-on by itself the entire folder of it needs to be zipped (See section #Installing)

### Installing

* Download the repository
* Zip the entire repository folder (root content of the zip is the single folder itself)
* Go within Blender to Preferences > Add-ons > Install Add-on > Select newly created zip file
* Should install successfully and a new tab called "LFR" should appear

## Initial Authors
* Serban Richardo
* Schmalzer Lukas

## Version History

* 0.1
    * Initial Release

## Known Issues:
  - Rotating a camera to rotate the projected image, does not work as expected
  - Trying to render multiple frames with Blender's Render -> Render Images or Render Animation
    option with EEVEE results in the program sometimes crashing. "GPU Texture Not Loaded" Error
  - The reason why it crashes may be due to how Blender deletes and applies images to the shader
    texture projection node. If the previous images would not be unallocated, the result would be
    in slowly allocating all the available amount of system RAM.
  - Current Workaround:
      - Switching to Cycles
      - Feature Set: Normal
      - Device: GPU Compute
  
## License

Copyright (c), FH OOE BAMBI

The code is licensed under an open source license.
