# AnythingTracker: Tracking Arbitrary Code Regions Across Different Versions

Given a code region in one commit, AnythingTracker finds the corresponding region in another commit. 

**Dependencies:**
  Python = ">=3.7", 
  GitPython~=3.1.31

### Data availability
Both datasets are available in the *data* directory.
* Subfolder *annotation* &emsp; The manually annotated dataset.
* File source_repo.txt &emsp; The collected 20 repositories (across 10 popular programming languages).
* Subfolder *suppression_data* &emsp; The suppression study dataset.
* File python repos.txt &emsp; The 8 Python repositories.
* Subfolder *results* &emsp; All the result files.
  * tracked_maps &emsp; Meta files of tracking results. 
  * execution_time &emsp; Meta files of execution times.
  * measurement_results &emsp; Files containing evaluation results.
  * table_plots &emsp; Result tables and figures.

## Experiments
### Tracking 
* **[AnythingTracker]** The entry point for tracking the datasets is located in the *src/anything_tracker/experiments* directory.
  * ComputeCandidatesForAnnoData.py &emsp; Tracking the manually annotated data. 
  * TrackHistoryPairsSuppression.py &emsp; Tracking the suppression study data.
* **[Baselines]** The entry point is located in the *src/anything_tracker/baselines* directory.
  * BaselineOnAnnoData.py &emsp; Tracking the manually annotated data. 
  * BaselineOnSuppression.py &emsp; Tracking the suppression study data.

### Evaluation
* Evaluation metrics: Overlapping, Exact matches, Partial overlaps, Character distance, Recall, Precision, and  F1-score.  
* The evaluation files are located in the *src/anything_tracker/measurement* directory.  
  * MeasureAnnotatedData.py &emsp; Check the results of the manually annotated data. 
  * MeasureSuppression.py &emsp; Check the results of the suppression study data.
 
* These files work for AnythingTracker and baselines and have 3 modes, the modes can be altered at the entry point of these files:
  * evaluating a specified approach, 
  * evaluating the approaches in the ablation study (turn off techniques or test context sizes).

### Visualization
All the result tables and plots are extracted from the files in the *src/anything_tracker/visualization* directory.

* **[Tables for RQ1]** TableAnnoSuppressionResults.py &emsp; Show the comparison with baselines. 
* **[Tables and Plots for RQ2]** 
  * PlotAnnoSuppressionResultsAblation.py &emsp; Show the results of the ablation study for turning off different components.
  * TableContextSizeResults.py &emsp; Show the results of the ablation study for testing different context sizes.
* **[Plot for RQ3]** PlotExexutionTimeComparison.py &emsp; Show the comparison of execution time with baselines.

## Reproducing the results in the paper
Choose between **SLOW MODE**, which runs AnythingTracker and baselines to track the datasets, runs the ablation study, and may take more than 30 minutes, including cloning the repositories, depending on the hardware, and **FAST MODE**, which generates the tables and plots (the ones in the RQ answering section) from pre-computed results and should take less than 5 minutes. 

**Note**: By default, the result files are stored in *data/result* and all verifications can be completed normally without modifying any path. 

### SLOW MODE
#### RQ1: Effectiveness of AnythingTracker. 
* **AnythingTracker**  
Specify to run/evaluate only AnythingTracker in the entry point.
  * Tracking
    * Run ComputeCandidatesForAnnoData.py 
    * Run TrackHistoryPairsSuppression.py
  * Evaluation
    * Run MeasureAnnotatedData.py 
    * Run MeasureSuppression.py 
* **Baselines**
  * Tracking
    * BaselineOnAnnoData.py
    * BaselineOnSuppression.py
  * Evaluation  
  Entry point - specify to start with *main_anythingtracker* and modify the folder name in *def main_anythingtracker* by adding a word *line* or *word* to the *results_dir* and *results_csv_file*.
    * Run MeasureAnnotatedData.py
    * Run MeasureSuppression.py 
* Run TableAnnoSuppressionResults.py -> Tables 2 and 3.

#### RQ2: Ablation study: impact of different components on AnythingTracker.
Specify to **run/evaluate**: (in the entry point of the files)
* starts with *main_anythingtracker* with option 3 **->** Test different context sizes.
* starts with *main_anythingtracker* and *context_line_num = 0*. **->** Disable context-aware similarity
* starts with *main_ablation_study* **->** Disable diff-based candidate extraction, movement detection, text search, and refinement of candidate regions, respectively, in one big experiment.
* Specifically: 
  * Tracking
    * Run ComputeCandidatesForAnnoData.py 
    * Run TrackHistoryPairsSuppression.py
  * Evaluation
    * Run MeasureAnnotatedData.py 
    * Run MeasureSuppression.py 
  * Run TableContextSizeResults.py -> Tables 4 and 5.
  * Run PlotAnnoSuppressionResultsAblation.py -> Figures 9 and 10.

#### RQ3: Efficiency of AnythingTracker.
* The execution time files are already there (*data/results/execution_time*) as the experiments in RQ1 are done. 
* Run PlotExexutionTimeComparison.py -> Figure 11.


### FAST MODE
By default, all the results tables and figures are in *data/results/table/plots*.  
All tables in results: Tables 2 and 3.  
All figures in results (exclude the example figures): Figures 7-9.  

* Run TableAnnoSuppressionResults.py -> Tables 2 and 3.
* Run TableContextSizeResults.py -> Tables 4 and 5.
* Run PlotAnnoSuppressionResultsAblation.py -> Figures 9 and 10.
* Run PlotExexutionTimeComparison.py -> Figure 11.
* Additionally, get the reported rates in RQ3 by running GetExexutionTimeRatio.py

