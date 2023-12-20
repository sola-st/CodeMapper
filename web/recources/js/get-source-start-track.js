// ***** part 1: get the selected source region *****
let selectedText;
let start;
let end;

document.getElementById("startTrack").onclick = function () {
  var selectedTextarea = document.getElementById('codeTextarea');
  selectedText = getSelectedText(selectedTextarea);
}

function getSelectedText(textarea) {
  start = textarea.selectionStart;
  end = textarea.selectionEnd;
  return textarea.value.substring(start, end);
}

// ***** part 2: run anything tracker to get the target region *****
/* 
call python functions to run the main tracking steps
Input: (from receive-text.js and current .js)
repoLink;
baseFileContent
targetFileContent
filePath; 
selectedText, start, end
*/

let target_region;

// TODO solve the "browser environment" issue
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
  target_region = data;
  console.log(`Target region: ${data}`);
});

// ***** part 3: highlight the target region, show results in webpage *****
// Escape special characters in the substring for regex
if (target_region == NaN){
  alert("A mapped region does not exists.");
}
else{
  // TODO highlight does not work
  var escapedSubstring = target_region.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  // Create a regex with the escaped substring
  var regex = new RegExp(escapedSubstring, "g");
  // Replace the substring with the highlighted version
  var highlightedText = targetFileContent.replace(regex, '<span id="highlightedText">$&</span>');
  // Display the highlighted text
  document.getElementById("targetCodeTextarea").innerHTML = highlightedText;
}