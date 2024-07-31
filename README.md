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

## Experiments
### Tracking 
* **[AnythingTracker]** The entry point for tracking the datasets is located in the *src/anything_tracker/experiments* directory.
  * ComputeCandidatesForAnnoData.py &emsp; Tracking the manually annotated data. 
  * TrackHistoryPairsSuppression.py &emsp; Tracking the suppression study data.
* **[Baselines]** The entry point is located in the *src/anything_tracker/baselines* directory.
  * BaselineOnAnnoData.py &emsp; Tracking the manually annotated data. 
  * BaselineOnSuppression.py &emsp; Tracking the suppression study data.

### Evaluation
* Evaluation metrics: Overlapping, Exact matches, Partial overlaps, Character distance, * Recall, Precision, and  F1-score.  
* The evaluation files are located in the *src/anything_tracker/measurement* directory.   
These files work for AnythingTracker and baselines.
  * MeasureAnnotatedData.py &emsp; Check the results of the manually annotated data. 
  * MeasureSuppression.py &emsp; Check the results of the suppression study data.

### Visualization
All the result tables and plots are extracted from the files in the *src/anything_tracker/visualization* directory.

* **[Tables for RQ1]** TableAnnoSuppressionResults.py &emsp; Show the comparison with baselines. 
* **[Tables for RQ2]** TableAnnoSuppressionResultsAblation.py &emsp; Show the results of the ablation study.
* **[Plot for RQ3]** PlotExexutionTimeComparison.py &emsp; Show the comparison of execution time with baselines.

## Reproducing the results in the paper
Choose between **SLOW MODE**, which runs AnythingTracker and baselines to track the datasets, runs the ablation study, and may take more than 30 minutes, including cloning the repositories, depending on the hardware, and **FAST MODE**, which generates the tables and plots (the ones in the RQ answering section) from pre-computed results and should take less than 5 minutes. 

**Note**: By default, the result files are stored in *data/result* and all verifications can be completed normally without modifying any path.

### SLOW MODE
#### RQ1: Effectivenes of AnythingTracker. 
* **AnythingTracker**
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
* Run TableAnnoSuppressionResults.py -> Tables II and III.

#### RQ2: Ablation study: impact of different components on AnythingTracker.
* Run 

#### RQ3: Efficiency of AnythingTracker.
* Run 


### FAST MODE
All tables in results: Tables ...  
All figures in results: Figures ...

