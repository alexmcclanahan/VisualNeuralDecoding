-------------------------------------------------------------------------
Visual Cortex Neural Decoding (Allen Institute) Code & Data Folder README
Author: Alexander McClanahan
-------------------------------------------------------------------------
General comments:
	*** If downloading this directory, will need to change all .py files (near the top of each file) to reflect where this entire directory is within the user's file system. ***
	*** The raw Allen Institute Neuropixels data is not contained herein, as the spike data alone is ~70 GB --> use DOWN_SPIKES.ipynb to pull down the Neuropixels data. ***
	*** Follow their tutorial to get set up with an ecephys_cache_dir and manifest.json file. ***


Contents:

	.py files:
		decoding_functions: set of modularized functions that are called within the three data scripts below
		decodeAlien.py: script that performs time binning analysis from each session within ecephys_cache_dir (not included due to size), per user input into the script where indicated; yields Excel files for Figure 4(A)
		decodeAlienAnat.py: script that performs 'local'/individual region decoding analysis from each session within ecephys_cache_dir (not included due to size), per user input into the script where indicated; yields Excel files for Figure 4(B)
		decodeAlienClumped.py: script that performs 'global'/clumped region decoding analysis from each session within ecephys_cache_dir (not included due to size), per user input into the script where indicated; yields Excel files for Figure 4(C)
		fourA.py: generates Figure 4(A) from data contained in Time_binning_figure directory
		fourAstats.py: performs user-specified statistical analysis on the data contained in Time_binning_figure directory
		fourB.py: generates Figure 4(B) from data contained in Local_anat_figure directory
		fourBstats.py: performs user-specified statistical analysis on the data contained in Local_anat_figure directory
		fourC.py: generates Figure 4(C) from Excel data contained in directories starting with 'All...'
		fourCstats.py: performs user-specified statistical analysis on the data contained in directories starting with 'All...'
		four.py: generates the combined Figure 4!
		DOWN_SPIKES.ipynb: this Jupyter notebook will pull down all Allen Institute Neuropixels data; may need some manual adjusting to this notebook
	
	Directories:
		Time_binning_figure: contains subdirectories of all time bins tested; inside of which are Excel files that contain the 				decoding accuracy outputs of decodeAlien.py 
		Local_anat_figure: contains subdirectories of all individual brain regions decoded from; inside of which are Excel files 			that contain the decoding accuracy outputs of decodeAlienAnat.py
		Global_anat_figure: *empty directory, as the fourC.py script runs easier if these grouped brain regions have separate 				folders in the main untitled4 directory (all directories starting with 'All...')
			depricated_figures: directory containing figures that have been 'retired' in the process of generating the final 			figures
		All_50_ms: Excel files that contain the decoding accuracy outputs of decodeAlienClumped.py using 'All' brain regions 				clumped together
		All V1 + LGN_50_ms: Excel files that contain the decoding accuracy outputs of decodeAlienClumped.py using only 'V1', 				'LGN'
		All Subcortical_50_ms: Excel files that contain the decoding accuracy outputs of decodeAlienClumped.py using only 				subcortical brain regions
		All Cortical_50_ms: Excel files that contain the decoding accuracy outputs of decodeAlienClumped.py using only cortical 			brain regions
