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

function highlightSourceRange(fileContent, range) {
  var startLine = range[0] - 1;
  var startChar = range[1] - 1;
  var endLine = range[2] - 1;
  var endChar = range[3];

  fileContent = fileContent.replace(/</g, "\&lt");
  fileContent = fileContent.replace(/>/g, "\&gt");
  var lines = fileContent.split('\n');
  for (var k = 0; k < lines.length; k++) {
    var line = lines[k];
    if (k === startLine && startLine === endLine) {
      if (endChar === line.length) {
        line = line.substring(0, startChar) + '<span class="highlight">' + line.substring(startChar, endChar) + '</span>';
      } else {
        line = line.substring(0, startChar) + '<span class="highlight">' + line.substring(startChar, endChar) + '</span>' + line.substring(endChar);
      }
    }
    else {
      if (k === startLine) {
        line = line.substring(0, startChar) + '<span class="highlight">' + line.substring(startChar);
      }
      if (k === endLine) {
        if (endChar === line.length) {
          line = line.substring(0, endChar) + '</span>' + line.substring(endChar);
        }else{
          line = line.substring(0, endChar) + '</span>';
        }
      }
    }

    lines[k] = line;
  }
  var currentRange = document.getElementById('fileInput').name;
  alert("Source region highlighted at: " + currentRange);
  console.log("Annotated source region: " + currentRange);

  // Reconstruct the paragraph with highlighted ranges
  var highlightedText = lines.join('\n');
  document.getElementById('codeTextarea').innerHTML = highlightedText;
}