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
      const fileContent = decodeURIComponent(escape(atob(data.content))); // atob(data.content);
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

function replaceSpecialMarks(fileContent) {
  fileContent = fileContent.replace(/</g, "\&lt");
  fileContent = fileContent.replace(/>/g, "\&gt");
  return fileContent;
}

function highlightSourceRange(fileContent, range) {
  var startLine = range[0] - 1;
  var startChar = range[1];
  var endLine = range[2] - 1;
  var endChar = range[3];

  var lines = fileContent.split('\n');
  var startOffset = lines.slice(0, startLine).join('\n').length + startChar;
  var endOffset = lines.slice(0, endLine).join('\n').length + endChar;

  var pre_text = fileContent.substring(0, startOffset);
  var highlight_text = fileContent.substring(startOffset, endOffset+1);
  var post_text = fileContent.substring(endOffset+1)

  var pre_to_display = replaceSpecialMarks(pre_text);
  var highlight_to_display = replaceSpecialMarks(highlight_text);
  var post_to_display = replaceSpecialMarks(post_text);
  var highlightedText = pre_to_display + '<span class="highlight">' + highlight_to_display + '</span>' + post_to_display

  alert("Source region highlighted at: [" + range + "]");
  console.log("Annotated source region: [" + range + "]");

  // Reconstruct the paragraph with highlighted ranges
  document.getElementById('codeTextarea').innerHTML = highlightedText;
}