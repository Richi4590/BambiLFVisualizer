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

### Getting started
* TBW
  
### Installing

* Download the repository
* TBW

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
