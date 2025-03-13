# CodeMapper: A Language-Agnostic Approach to Code Region Tracking

Given a code region in one commit, CodeMapper finds the corresponding region in another commit. 

**Dependencies:**
  * Python = ">=3.7"
  * GitPython~=3.1.31
  * tree-sitter 
    * Run ```pip install -r requirements.txt``` in the root directory of this project.

### Data availability
All datasets are available in the *data* directory.
* Subfolder *annotation* &emsp; The annotated datasets.
* File source_repo.txt &emsp; The collected 20 repositories (across 10 popular programming languages).
* Subfolder *suppression_data* &emsp; The suppression study dataset.
* File python repos.txt &emsp; The 8 Python repositories.
* Subfolder *results* &emsp; All the result files.
  * tracked_maps &emsp; Meta files of tracking results. 
  * execution_time &emsp; Meta files of execution times.
  * measurement_results &emsp; Files containing evaluation results.
  * table_plots &emsp; Result tables and figures.

## Experiments
_* Note: Some folders are named 'anything_tracker' instead of 'CodeMapper' because the name was changed during development, but the older name is still used in some parts of the code._
### Tracking 
* **[CodeMapper]** Directory: *src/anything_tracker/experiments*
  * ComputeCandidatesForAnnoData.py &emsp; Tracking the annotated data A and B. 
  * TrackHistoryPairsSuppression.py &emsp; Tracking the suppression study data.
* **[Baselines]** The entry point is located in the *src/anything_tracker/baselines* directory.
  * BaselineOnAnnoData.py &emsp; Tracking the manually annotated data. 
  * BaselineOnSuppression.py &emsp; Tracking the suppression study data.

* **[Ablation studies]**
  * **[Disabling components]**  Directory: *src/anything_tracker/experiments/ablation/components*
    * DisableComponentAnnodata.py &emsp; Run an abation study to disable each component on the annotated data A and B. 
    * DisableComponentSuppression.py &emsp; Run an abation study to disable each component on the suppression data. 
  * **[Various context sizes]**  Directory: *src/anything_tracker/experiments/ablation/context*
    * VariousContextSizesAnnodata.py &emsp; Run an abation study to track with various context sizes on the annotated data A and B. 
    * VariousContextSizesSuppression.py &emsp; Run abation study to track with various context sizes on the suppression data. 

### Evaluation
* **[Evaluation metrics]** Overlapping, Exact matches, Partial overlaps, Character distance, Recall, Precision, and  F1-score.  
* **[Measurement]** Directory: *src/anything_tracker/measurement*. These two files work for CodeMapper and baselines.
  * MeasureAnnotatedData.py &emsp; Check the results of the annotated data A and B. 
  * MeasureSuppression.py &emsp; Check the results of the suppression study data.

* **[Evaluate ablation studies]**
  * **[Components]** Directory: *src/anything_tracker/measurement/ablation/components*
    * ComponentMeasureAnnodata.py &emsp; Check the ablation study results of the annotated data A and B. 
    * ComponentMeasureSuppression.py &emsp; Check the ablation study results of the suppression study data.
  * **[Context sizes]** Directory: *src/anything_tracker/measurement/ablation/context*
    * ContextMeasureAnnodata.py &emsp; Check the ablation study results of the annotated data A and B. 
    * ContextMeasureSuppression.py &emsp; Check the ablation study results of the suppression study data.

### Visualization
All the result tables and plots are extracted from the files in the *src/anything_tracker/visualization* directory.

* **[Tables for RQ1]** TableAnnoSuppressionResults.py &emsp; Show the comparison with baselines. 
* **[Plots for RQ2]** 
  * PlotAnnoSuppressionResultsAblation.py &emsp; Show the results of the ablation study for disabling different components.
  * PlotContextSizeResults.py &emsp; Show the results of the ablation study for testing different context sizes.
* **[Plot for RQ3]** PlotExexutionTimeComparisonDetailed.py &emsp; Show the comparison of execution time with baselines.

## Reproducing the results in the paper
Choose between **SLOW MODE**, which runs CodeMapper and baselines to track the datasets, runs the ablation study, and may take more than 30 minutes, including cloning the repositories, depending on the hardware, and **FAST MODE**, which generates the tables and plots (the ones in the RQ answering section) from pre-computed results and should take less than 5 minutes. 

**Notes**:
* By default, the result files are stored in *data/result* and all verifications can be completed normally without modifying any path. 
* By default, all the results tables and figures are in *data/results/table/plots*. 
* Check the [Experiments](#experiments) to locate files.

### SLOW MODE
#### RQ1: Effectiveness of CodeMapper. 
* **CodeMapper**  
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
    * Run MeasureAnnotatedData.py
    * Run MeasureSuppression.py 
* Run TableAnnoSuppressionResults.py -> Tables 2, 3 and 4.

#### RQ2: Ablation study: Impact of Different Components and Parameters of CodeMapper
* **Disabling components** 
  * Tracking
    * Run DisableComponentAnnodata.py
    * Run DisableComponentSuppression.py
  * Evaluation
    * ComponentMeasureAnnodata.py 
    * ComponentMeasureSuppression.py
* **Various context sizes** 
  * Tracking 
    * VariousContextSizesAnnodata.py 
    * VariousContextSizesSuppression.py 
  * Evaluation
    * ContextMeasureAnnodata.py 
    * ContextMeasureSuppression.py

* Run PlotContextSizeResults.py -> Figure 9.
* Run PlotAnnoSuppressionResultsAblation.py -> Figure 10.

#### RQ3: Efficiency of CodeMapper.
* The execution time files are already there (*data/results/execution_time*) as the experiments in RQ1 are done. 
* Run PlotExexutionTimeComparisonDetailed.py   
  -> Figure 11.  
  -> It also generates a .json file (the same folder as Figure 11) which records the ratio of each step.


### FAST MODE
By default, all the results tables and figures are in *data/results/table/plots*.  
All tables in results: Tables 2, 3, and 4.  
All figures in results (exclude the motivation/example figures): Figures 9, 10, and 11.  
The following files are in the *src/anything_tracker/visualization* directory.
* Run TableAnnoSuppressionResults.py -> Tables 2, 3 and 4.
* Run PlotContextSizeResults.py -> Figure 9.
* Run PlotAnnoSuppressionResultsAblation.py -> Figure 10.
* Run PlotExexutionTimeComparisonDetailed.py  
  -> Figure 11.  
  -> It also generates a .json file (the same folder as Figure 11) which records the ration of each step.

