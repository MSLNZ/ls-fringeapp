# ls-fringeapp
for processing gauge block interferograms

TODO

    [ ] investigate warning given by testfile2frac
    [ ] investigate 0.4e-3 relative difference in fringe fraction between this version and 2016 runs
         the uncertainty for finrge fraction is 2 * 2.3 nm/633 nm = 0.0073 whics is much larger 
         than 0.0004
    [ ] use xml file for wavelengths

    TODO features
    
    [ ] able to process red images without green images. Issue #1
    
    TODO bugs
    [ ] redo is not working?

    TODO refactoring
    run Black  
    [x]  fringeprocess.py
    [x] gauge_length.py
    [x ] FringeApp03.py
    [ ] tkinter application window should be in main
    
    TODO testing
    [x] overall continuity of results test for array2frac
    [ ] tests for CalcGaugeLength
    [ ] tests for RefractiveIndex
    
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
 [ ]                 .calculate_output
                  
 [ ]    gauge_length.calcgaugelength
                   
    
 >>> import Tkinter, tkFileDialog
>>> root = Tkinter.Tk()
>>> root.withdraw()
''
>>> dirname = tkFileDialog.askdirectory(parent=root,initialdir="/",title='Pick a directory')

https://stackoverflow.com/questions/1406145/how-do-i-get-rid-of-python-tkinter-root-window