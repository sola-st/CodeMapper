# Usage of the Annotation tool
### Annotation tool can be run locally or by using Flask framework:
- Local: web/resources/templates/index.html  
- Flask: web/resources/app.py

### The main page (index.html) includes 4 big areas:  
- Title area
- Meta information area (shows git URL, commits, and file names)
- Main area
    - Version names
    - Source and target file contents
- Function buttons

### Detailed steps:  
- **Click the button "Choose file"** to select the JSON file which includes the meta information of the to-annotate data.
    - It supports the format of "to_annatate" and "annotated" data.
    - For the annotated data, it will automatically highlight the annotated source range.
    - If you select some new ranges for the source version, the highlighted annotated source range will disappear. If needed, click the "Load Data" button to get the annotated source range back.
- **Click the button "Read"** to read the first piece of data and start annotation.
    - The title area will show:
        - A table that counts the cases of neighboring commits, k-distance commits, and the size categories.
        - A table that counts different change types, and shows the total number of all annotated data.
    - The meta-information area will show the metadata.
    - the Version name area will show additional information. 
        - The index of current data (starts at 1),
        - change type,
        - commit distance,
        - the size of source regions, 
        - the time order of the ranges,
        - and some other marks. It is designed for data creators, which allows them to record what happens in the range pairs. It can be empty. For example, they can write "The lines are wrapped in an if-statement".
- **Click the button "Load Data"**.
    - The source and target file contents will be shown in the text boxes.
- **Annotation**.
    - Read the source and target files. If the contents are meaningless, click the button "Next" to skip the current one.
    - **Select the source and target ranges**. 
        - If the ranges are highlighted in colors, they are successfully selected. 
        - The highlighted ranges are temporarily stored, If you want to pick up a new one, just select the range again, it will overwrite the old one.
    - Select the change operation, size category and write marks for current range pairs.
    - **Click the button "Push"** to temporarily store current annotated ranges.
    - The annotated ranges will not be written to a local file until you click the button "Save Annotation". You can write annotated data to a local file at any time you want.
    - Click "Next" to annotate the next piece of data. 
- **Write annotated data to a local file**
    - **Click the button "Save Annotation"**.

