let repoLink;
let sourceCommit;
let targetCommit;
let sourceFilePath;
let HighlightedDiv = document.getElementById('codeTextarea');
let targetHighlightedDiv = document.getElementById('targetCodeTextarea');

document.getElementById("loadData").onclick = function(){
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
      const formattedContent = formatCodeContent(fileContent);
      if (target == false) {
        HighlightedDiv.innerHTML = formattedContent;
        updateLineNumbers();
      } else {
        targetHighlightedDiv.innerHTML = formattedContent;
        updateLineNumbersTarget();
      }
     
    })
    .catch(error => {
      console.error('Error fetching file content:', error);
    });
}

function formatCodeContent(content) {
  // Replace leading spaces with non-breaking space entities
  const indentedContent = content.replace(/^( +)/gm, match => {
    return '&nbsp;'.repeat(match.length);
  });
  // Replace newline characters with <br> tags
  return indentedContent.replace(/\n/g, '<br>');
}


// // usage example
// https://github.com/Hhyemin/suppression-test-python-mypy
// 19b9ff4
// bb01e91
// src/compare/find_max.py