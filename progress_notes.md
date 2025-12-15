# ls-fringeapp
for processing gauge block interferograms

TODO

    [ ] investigate warning given by testfile2frac
    [ ] investigate 0.4e-3 relative difference in fringe fraction between this version and 2016 runs
         the uncertainty for finrge fraction is 2 * 2.3 nm/633 nm = 0.0073 whics is much larger 
         than 0.0004
    [x] use xml file for wavelengths

    TODO features
    
    [x]  able to process red images without green images. Issue #1
    [x]  use separate temperatures for air and gauge block Issue #2 requires more columns in load
    [x]  write out wavelengths, refractive index 
    [ ]  fail gracefully if wrong number of columns in file
    TODO bugs
    [x] redo is not working?
    [x] better directory handling - including looking at actual file not onw in cropped directory
    [x] if a full filename is not given assume it is in same directory as input file
    

    TODO refactoring
    run Black  
    [x]  fringeprocess.py
    [x] gauge_length.py
    [x ] FringeApp03.py
    
    [x] tkinter application window should be in init
    [x] the test for red_green should use the filename
    
    TODO testing
    [x] overall continuity of results test for array2frac
    [x] tests for CalcGaugeLength
    [x] test for calcgaugelength that include separate air temp
    [x] test for calcgaugelength_red_only
    [ ] tests for RefractiveIndex - there are some in the main part of the file
    [ ] tests for reading and writing files
    
    Unit tests
        gauge_length.py  
        [ ] CalcGaugeLength  
        [ ] frac  
        
        fringe_process.py  
        [ ] findpeaks2  
        [ ] pkfind   
        [ ] findfringes2  
        [ ] findfringes4E  
        [ ] lines2frac  
        [ ] shifthalf  
        [ ] roipoly  
        [ ] gbroif  
        [ ] array2frac  
        
        [ ] refractiveindex

Calling structure

    FringeManager.load_gauge_data
        open_image
        process_image 

    FringeManager.process_image
        array2frac
            gbroif
                roipoly
            pkfind
                findpeaks2
            findfringes2            
            findfringes4E
            lines2frac
                shifthalf
                
    FringeManager.calculate_output
        CalcGaugeLength
            frac
            refractiveindex
            
 
        
 Green Image dependent
   
 [x]    FringeManager.load_gauge_data
 [x]                 .calculate_output
                  
 [x]    gauge_length.calcgaugelength
                   
    
 >>> import Tkinter, tkFileDialog
>>> root = Tkinter.Tk()
>>> root.withdraw()
''
>>> dirname = tkFileDialog.askdirectory(parent=root,initialdir="/",title='Pick a directory')

https://stackoverflow.com/questions/1406145/how-do-i-get-rid-of-python-tkinter-root-window

File structure now includes air temperature for red and green

The read only file structure only has data pertaining to red


## 2025-12-15

New code that allows analysis of fringe images for square gauges with a central round hole.

The previous code is archived in the `pre-square-gauge-code` branch.

I've also changed the code layout to a `src layout` to make it easier to work with the uv package manager.

The starting point of the code is in `src/ls_fringeapp/FringeApp03.py`.  
`uv run ls_fringeapp` will run the code in `src/ls_fringeapp/__init__.py` which just creates an instance of the `FringeManager` class from `src/ls_fringeapp/FringeApp03.py`. If running without `uv` ( from an IDE for instance), just run `FringeApp03.py`

- `src/ls_fringeapp/file_formats.py` - definition of the file formats for csv files
- `src/ls_fringeapp/FringeApp03.py` - main `FringeManager` class
- `src/ls_fringeapp/fringeprocess.py` - code to process fringe images - not dependent on GUI.
- `src/ls_fringeapp/gauge_length.py` - calculate gauge length from fringe fractions and gauge data - not dependent on GUI
- `src/ls_fringeapp/load_equipment_data.py` - load the red and green wavelengths for equipment register - separate for easy updates
- `src/ls_fringeapp/plot_helpers.py` - function for annotation image outside  `FringeManager` - used in  notebooks
- `src/ls_fringeapp/poly_lasso.py` - code to provide the gauge selection widget used in the matplotlib gauge image
- `src/ls_fringeapp/refractiveindex.py` - calculation of the refractive of air for wavelength and air temperature, pressure and humidity
- `src/ls_fringeapp/synthetic_images.py` - code to produce synthetic images - used intest and notebooks
- `tests` - test for code - run with `pytest`
- `tests/data` - fringe images etc to use with tests and notebooks
- `notebooks` - jupyter notebooks used during code development


# Code History
This code goes way back to some old matlab code (2002) written in conjunction with Lionel Watkins and Sze Tan then at the  Department of Physics, Auckland University.   
see:  
Howick, E.F.; Watkins, L.R.; Tan, S.M. 2003. Automation of a 1960's Hilger gauge block interferometer. Metrologia. Vol.40 (4),

Eleanor Howick translated it to python in ~2009. (May have been earlier). All mistakes are probably mine.

The code uses matplotlib for the GUI, (historical reasons - what was avaliable/known at the time) with some Tkinter dialogs. Is a bit of an odd design but mostly works. I've resisted desires to rewrite in something a bit more modern or flexible.