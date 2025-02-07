# Usage of the Annotation tool
### Annotation tool can be run locally or by using Flask framework:
- Local: web/resources/templates/index.html  
- Flask: web/resources/app.py  

**[Important] GitHub token setting.**
- Escapes the 60 requests per hour limit.
- Now the token is read from the environment variables: (lines 21--23 of file _web/resources/static/receive-text.js_.)
```
const headers = {
  Authorization: `token ${process.env.GITHUB_TOKEN}`,
};
```
If this does not work on your machine, **check the environment variable name or hardcode it if needed.**
 

### The main page (index.html) includes 4 big areas:  
- Title area
- Meta information area (shows git URL, commits, and file names)
- Main area
    - Version names
    - Change opertation, Character distance, Source region category
    - Time order, Editable textbox to leave notes
    - Source and target file contents
- Function buttons

## Detailed steps:  
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
    - **Note: For annotated source regions:**
        - It pops up an alert window to show the highlight range, which helps users quickly locate the highlight.
        - The annotated range is also recorded in the log message.
- **Click the button "Load Data"**.
    - The source and target file contents will be shown in the text boxes.

- ### Annotated dataset A
    - **Annotation 1st round**.
        - Read the source and target files. If the contents are meaningless, click the button "Next" to skip the current one.
        - **Select the source and target ranges**. 
            - If the ranges are highlighted in colors, they are successfully selected. 
            - The highlighted ranges are temporarily stored, If you want to pick up a new one, just select the range again, it will overwrite the old one.
        - Select the change operation, size category and write marks for current range pairs.
        - **Click the button "Push"** to temporarily store current annotated ranges.
        - The annotated ranges will not be written to a local file until you click the button "Save Annotation". You can write annotated data to a local file at any time you want.
        - Click "Next" to annotate the next piece of data. 
    - **Annotation 2nd round [Validation]**.
        - The source region is automatically highlighted. 
        - For the additional information in the Version name area:
            - You must pick up a change type for your validation.
            - You can use the marker input box to write some notes about the validated differences.
            - The other items (like commit distance, time order, and the size of source regions) are fixed, they are read from the annotated data.  
            - **NOTES**: If you have different opinions on the size of source regions, you can choose a new one for it.
        - Select the target ranges. 
        - Click the button "Push" to temporarily store current annotated ranges.
        - Click "Next" to annotate the next piece of data. 

    - **Write annotated data to a local file**
        - **Click the button "Save Annotation"**. 
            - Writing a file **will clear the storage** of the tool. For example, if you write the file once at 20 cases, and then again at 40 cases, this so-called 40 will not contain the first 20 cases that have been written before, which means the second round of writing just writes the remaining 20.
            - According to the design, when switching to read files in different formats (switch between "to_annotate.json" and "annotated.json"), you should:
                - save the current annotation data locally, and
                - refresh the window to start a new round of reading.

- ### Annotated dataset B
    - The source region is automatically highlighted. 
    - **Select target ranges**. 
        - If the ranges are highlighted in colors, they are successfully selected. 
        - The highlighted ranges are temporarily stored, If you want to pick up a new one, just select the range again, it will overwrite the old one.
    - All other terms (e.g., change operation, size category) are auto-generated and displayed. You can write marks for current range pairs if desired.
    - **Click the button "Push"** to temporarily store current annotated ranges.
    - The annotated ranges will not be written to a local file until you click the button "Save Annotation". You can write annotated data to a local file at any time you want.
    - **Click "Next"** to annotate the next piece of data. 

    - **Click the button "Save Annotation"**. 
        - Writing a file **will not clear the storage** of the tool. For example, if you write the file once at 20 cases, and then again at 40 cases, this 40 will contain the first 20 cases that have been written before.
