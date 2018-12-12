# ls-fringeapp
for processing gauge block interferograms

TODO refactoring  
[x] run Black fringeprocess.py
[ ] gauge_length.py
[ ] FringeApp03.py

TODO testing
[ ] overall continuity of results test
[ ] unit tests

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