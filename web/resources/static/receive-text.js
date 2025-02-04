let repoLink;
let sourceCommit;
let targetCommit;
let sourceFilePath;
let HighlightedDiv = document.getElementById('codeTextarea');
let targetHighlightedDiv = document.getElementById('targetCodeTextarea');

document.getElementById("loadData").onclick = function () {
  repoLink = document.getElementById('repo').value;
  sourceCommit = document.getElementById('sourceCommit').value;
  targetCommit = document.getElementById('targetCommit').value;
  sourceFilePath = document.getElementById('sourceFilePath').value;
  targetFilePath = document.getElementById('sourceFilePath').value;
  let user_repo_name = repoLink.replace(/^https:\/\/github\.com\//, '');
  const baseUrl = `https://api.github.com/repos/${user_repo_name}/contents/${sourceFilePath}?ref=${sourceCommit}`;
  getFileContents(baseUrl);
  const targetUrl = `https://api.github.com/repos/${user_repo_name}/contents/${targetFilePath}?ref=${targetCommit}`;
  getFileContents(targetUrl, true);
}

function getFileContents(url, target = false) {
  fetch(url)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Network response was not ok: ${response.statusText}`);
      }
      return response.json();
    })
    .then(data => {
      const fileContent = atob(data.content);
      if (target == false) {
        HighlightedDiv.innerText = fileContent;
        updateLineNumbers();
        var range = document.getElementById('fileInput').name;
        if (range != "round1"){
          if (range.includes(",")) {
            highlightSourceRange(fileContent, JSON.parse(range))
          } else{
            alert("No source region");
            console.log("Annotated source region: null");
          }
        }
      } else {
        targetHighlightedDiv.innerText = fileContent;
        updateLineNumbersTarget();
      }

    })
    .catch(error => {
      console.error('Error fetching file content:', error);
    });
}

function countOccurrences(mainStr) {
  smaller_than_counts = mainStr.split(/</g).length - 1
  greater_than_counts = mainStr.split(/>/g).length - 1
  return smaller_than_counts + greater_than_counts;
}

function updateChars(ori_line, startChar, endChar){ // the startChar and endChar on the ori_line
  var beforeStartCount = countOccurrences(ori_line.substring(0, startChar))
  startChar += beforeStartCount * 2
  var toHighlight = countOccurrences(ori_line.substring(startChar, endChar))
  endChar += toHighlight * 2;
  return startChar, endChar; // the position on the corresponding dispaly line
}

function replaceSpecialMarks(fileContent) {
  fileContent = fileContent.replace(/</g, "\&lt");
  fileContent = fileContent.replace(/>/g, "\&gt");
  return fileContent;
}

function highlightSourceRange(fileContent, range) {
  var startLine = range[0] - 1;
  var startChar = range[1] - 1;
  var endLine = range[2] - 1;
  var endChar = range[3];
  var fileContentOri = fileContent; // for checking highlight ranges

  // for display 
  fileContent = fileContent.replace(/</g, "\&lt");
  fileContent = fileContent.replace(/>/g, "\&gt");

  var ori_lines = fileContentOri.split('\n');
  var display_lines = fileContent.split('\n');
  for (var k = 0; k < display_lines.length; k++) {
    var ori_line = ori_lines[k]; // for position checking
    var display_line = display_lines[k]; // for display
    // startChar, endChar is the char position on original file contents
    // startCharDisplay, endCharDisplay is the position on the displayed version file contents
    var startCharDisplay = startChar;
    var endCharDisplay = endChar;
    if (ori_line.length < display_line.length){
      startCharDisplay, endCharDisplay = updateChars(ori_line, startChar, endChar);
    }
    if (k === startLine && startLine === endLine) {
      if (endChar === ori_line.length) {
        display_line = display_line.substring(0, startCharDisplay) + '<span class="highlight">' + display_line.substring(startCharDisplay, endCharDisplay) + '</span>';
      } else {
        display_line = display_line.substring(0, startCharDisplay) + '<span class="highlight">' + display_line.substring(startCharDisplay, endCharDisplay) + '</span>' + display_line.substring(endCharDisplay);
      }
    }
    else {
      if (k === startLine) {
        display_line = display_line.substring(0, startCharDisplay) + '<span class="highlight">' + display_line.substring(startCharDisplay);
      }
      if (k === endLine) {
        if (endChar === ori_line.length) {
          display_line = display_line.substring(0, endCharDisplay) + '</span>';
        }else{
          display_line = display_line.substring(0, endCharDisplay) + '</span>'+ display_line.substring(endCharDisplay);
        }
      }
    }

    display_lines[k] = display_line;
  }

  var currentRange = document.getElementById('fileInput').name;
  alert("Source region highlighted at: " + currentRange);
  console.log("Annotated source region: " + currentRange);

  // Reconstruct the paragraph with highlighted ranges
  var highlightedText = display_lines.join('\n');
  document.getElementById('codeTextarea').innerHTML = highlightedText;
}