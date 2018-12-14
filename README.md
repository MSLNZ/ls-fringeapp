# ls-fringeapp
for processing gauge block interferograms

TODO

    [ ] investigate warning given by testfile2frac
    [ ] investigate 0.4e-3 relative difference in fringe fraction between this version and 2016 runs


    TODO refactoring
    run Black  
    [x]  fringeprocess.py
    [x] gauge_length.py
    [x ] FringeApp03.py
    
    TODO testing
    [x] overall continuity of results test for array2frac
    [ ] tests for CalcGaugeLength
    
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