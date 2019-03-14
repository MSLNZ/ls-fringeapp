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