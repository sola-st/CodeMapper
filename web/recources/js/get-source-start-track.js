let selectedText;
let start;
let end;

document.getElementById("startTrack").onclick = function(){
    var selectedTextarea = document.getElementById('codeTextarea');
    selectedText = getSelectedText(selectedTextarea);
    console.log(selectedText);
    alert('Selected text: ' + selectedText);
  }

function getSelectedText(textarea) {
    start = textarea.selectionStart;
    end = textarea.selectionEnd;
    return textarea.value.substring(start, end);
}

/* 
call python functions to run the main tracking steps
Input: (from receive-text.js and current .js)
repoLink;
baseFileContent
targetFileContent
filePath; 
selectedText, start, end
*/

const fs = require('fs');
const process = require('child_process');
const child_process = process.spawn('python3', 
                ['src/anything_tracker/AnythingTrackerUI.py',
                  baseFileContent,
                  targetFileContent,
                  start,
                  end,
                  selectedText
                ]);
child_process.stdout.on('data', (data) => {
  console.log(`Candidate regions: ${data}`);
});

child_process.on('close', (code) => {
  console.log(`Python exited with ${code}`);
});