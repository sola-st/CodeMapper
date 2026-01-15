# CodeMapper: A Language-Agnostic Approach to Mapping Code Regions Across Commits

CodeMapper address the code mapping problem in a way that is independent of specific program elements and programming languages. Given a code region in one commit, CodeMapper finds the corresponding region in another commit. 
To have a comprehensive understanding of this work, you can check out our [research paper](https://software-lab.org/publications/icse2026_CodeMapper.pdf) here.
The artifact has been archived on Zenodo to ensure long-term availability and can be accessed at: 

### Setup
Choose one of the following options to set up the project:

**Option 1: Run locally**  
If you prefer to run the code locally, make sure you have python>=3.7, and run the following from the root directory of this project:
  1. `pip install -r requirements.txt`  
    For [fast mode](#fast-mode), the requirements can be reduced to only `numpy` and `matplotlib`.
  2. `pip install -e .`

**Option 2: Run with Docker**  
If you prefer to isolate the packages that you install during the reproduction, use Docker.
1. Install Docker (if it is your first time using Docker, [Docker Desktop](https://docs.docker.com/desktop/) is recommended)
2. Build the image: `docker build -t codemapper .`  
3. Run the container with files editable: `docker run -it -v $(pwd):/codemapper_home codemapper`
    <!-- * With files non-editable: `docker run -it codemapper` -->

### Data availability
All datasets are available in the *data* directory.
* Subfolder *annotation* &emsp; The annotated datasets and CodeTracker data.
* File source_repo.txt &emsp; The collected 20 repositories (across 10 popular programming languages).
* File source_repo_java.txt &emsp; The 10 repositories for Java (CodeTracker data).
* Subfolder *suppression_data* &emsp; The suppression study dataset.
* File python repos.txt &emsp; The 8 Python repositories.
* Subfolder **results** &emsp; [Load pre-computed results](#load-pre-computed-results) &emsp; All the result files.
  * tracked_maps &emsp; Meta files of tracking results. 
  * execution_time &emsp; Meta files of execution times.
  * measurement_results &emsp; Files containing evaluation results.
  * table_plots &emsp; Result tables and figures.

## Experiments
_* Note: Some folders are named 'anything_tracker' instead of 'CodeMapper' because the name was changed during development, but the older name is still used in some parts of the code._
### Tracking 
* **[CodeMapper]** Directory: *src/anything_tracker/experiments*
  * TrackHistoryPairsAnnoData.py &emsp; Tracking the annotated data A and B. 
  * TrackHistoryPairsSuppression.py &emsp; Tracking the suppression study data.
  * TrackHistoryPairsTrackerData.py &emsp; Tracking the CodeTracker data.
* **[Baselines]** The entry point is located in the *src/anything_tracker/baselines* directory.
  * BaselineOnAnnoTrackerData.py &emsp; Tracking the annotated data and CodeTracker data. 
  * BaselineOnSuppression.py &emsp; Tracking the suppression study data.

* **[Ablation studies]**
  * **[Disabling components]**  Directory: *src/anything_tracker/experiments/ablation/components*
    * DisableComponentAnnodata.py &emsp; Run an abation study to disable each component on the annotated data A and B. 
    * DisableComponentSuppression.py &emsp; Run an abation study to disable each component on the suppression data. 
    * DisableComponentTrackerData.py &emsp; Run an abation study to disable each component on the CodeTracker data. 
  * **[Various context sizes]**  Directory: *src/anything_tracker/experiments/ablation/context*
    * VariousContextSizesAnnodata.py &emsp; Run an abation study to track with various context sizes on the annotated data A and B. 
    * VariousContextSizesSuppression.py &emsp; Run abation study to track with various context sizes on the suppression data. 
    * VariousContextSizesTrackerData &emsp; Run abation study to track with various context sizes on the CodeTracker data. 

### Evaluation
* **[Evaluation metrics]** Overlapping, Exact matches, Partial overlaps, Character distance, Recall, Precision, and  F1-score.  
* **[Measurement]** Directory: *src/anything_tracker/measurement*. These two files work for CodeMapper and baselines.
  * MeasureAnnoTrackerData.py &emsp; Check the results of the annotated data A and B, and the CodeTracker data. 
  * MeasureSuppression.py &emsp; Check the results of the suppression study data.

* **[Evaluate ablation studies]**
  * **[Components]** Directory: *src/anything_tracker/measurement/ablation/components*
    * ComponentMeasureAnnoTrackerData.py &emsp; Check the ablation study results of the annotated data A and B, and the CodeTracker data. 
    * ComponentMeasureSuppression.py &emsp; Check the ablation study results of the suppression study data.
  * **[Context sizes]** Directory: *src/anything_tracker/measurement/ablation/context*
    * ContextMeasureAnnoTrackerData.py &emsp; Check the ablation study results of the annotated data A and B, and the CodeTracker data. 
    * ContextMeasureSuppression.py &emsp; Check the ablation study results of the suppression study data.

### Visualization
All the result tables and plots are extracted from the files in the *src/anything_tracker/visualization* directory.

* **[Tables for RQ1]** TableAnnoSuppressionResults.py &emsp; Show the comparison with baselines. 
* **[Plots for RQ2]** 
  * PlotAnnoSuppressionResultsAblation.py &emsp; Show the results of the ablation study for disabling different components.
  * PlotContextSizeResults.py &emsp; Show the results of the ablation study for testing different context sizes.
* **[Plot for RQ3]** PlotExexutionTimeComparisonDetailed.py &emsp; Show the comparison of execution time with baselines.

## Reproducing the results in the paper
Choose between **SLOW MODE**, which runs CodeMapper and baselines to track the datasets, runs the ablation study, and may take serveral hours, including cloning the repositories, depending on the hardware, and **FAST MODE**, which generates the tables and plots (the ones in the RQ answering section) from pre-computed results and should take less than 5 minutes. 

**Notes**:
* By default, the result files are stored in *data/result* and all verifications can be completed normally without modifying any path. 
* By default, all the results tables and figures are in *data/results/table_plots*. 
* Check the [Experiments](#experiments) to locate files.

### SLOW MODE
#### RQ1: Effectiveness of CodeMapper. 
* **CodeMapper**  
  * Tracking
    * Run TrackHistoryPairsAnnoData.py 
    * Run TrackHistoryPairsSuppression.py
    * Run TrackHistoryPairsTrackerData.py
  * Evaluation
    * Run MeasureAnnoTrackerData.py 
    * Run MeasureSuppression.py 
* **Baselines**
  * Tracking
    * BaselineOnAnnoTrackerData.py
    * BaselineOnSuppression.py
  * Evaluation  
    * Run MeasureAnnoTrackerData.py
    * Run MeasureSuppression.py 
* Run TableAnnoSuppressionResults.py -> Tables 2 and 3.

#### RQ2: Ablation study: Impact of Different Components and Parameters of CodeMapper
* **Disabling components** 
  * Tracking
    * Run DisableComponentAnnodata.py
    * Run DisableComponentSuppression.py
    * Run DisableComponentTrackerData.py
  * Evaluation
    * ComponentMeasureAnnoTrackerData.py 
    * ComponentMeasureSuppression.py
* **Various context sizes** 
  * Tracking 
    * VariousContextSizesAnnodata.py 
    * VariousContextSizesSuppression.py 
    * VariousContextSizesTrackerData.py
  * Evaluation
    * ContextMeasureAnnoTrackerData.py 
    * ContextMeasureSuppression.py

* Run PlotContextSizeResults.py -> Figure 10.
* Run PlotAnnoSuppressionResultsAblation.py -> Figure 11.

#### RQ3: Efficiency of CodeMapper.
* The execution time files are already there (*data/results/execution_time*) as the experiments in RQ1 are done. 
* Run PlotExexutionTimeComparisonDetailed.py   
  -> Figure 12.  
  -> It also generates a .json file (the same folder as Figure 12) which records the ratio of each step.


### FAST MODE
**Load pre-computed results**  
Before generate the table and plots, load the pre-computed results. Here are two options:

* [Option 1] Run LoadPreComputedResults.py, it will automatically load and place the results folder in the correct location.
* [Option 2] Manually download results.zip from the latest release and extract it into the data folder.
You can check the structure of data/results here.

By default, all the results tables and figures are in *data/results/table_plots*.  
All tables in results: Tables 2, 3.  
All figures in results (exclude the motivation/example figures): Figures 10, 11, and 12.  
The following files are in the *src/anything_tracker/visualization* directory.
* Run TableAnnoSuppressionResults.py -> Tables 2 and 3.
* Run PlotContextSizeResults.py -> Figure 10.
* Run PlotAnnoSuppressionResultsAblation.py -> Figure 11.
* Run PlotExexutionTimeComparisonDetailed.py  
  -> Figure 12.  
  -> It also generates a .json file (the same folder as Figure 12) which records the ration of each step.

