let repoLink;
let baseCommit;
let targetCommit;
let filePath;

let baseFileContent;
let targetFileContent;

document.getElementById("loadData").onclick = function(){
  repoLink = document.getElementById('repo').value;
  baseCommit = document.getElementById('baseCommit').value;
  targetCommit = document.getElementById('targetCommit').value;
  filePath = document.getElementById('filePath').value;

  let user_repo_name = repoLink.replace(/^https:\/\/github\.com\//, '');
  const baseUrl = `https://api.github.com/repos/${user_repo_name}/contents/${filePath}?ref=${baseCommit}`;
  const codeTextarea = document.getElementById('codeTextarea');
  getFileContents(baseUrl)
  // // console.log(baseUrl)

  const targetUrl = `https://api.github.com/repos/${user_repo_name}/contents/${filePath}?ref=${targetCommit}`;
  const targetCodeTextarea = document.getElementById('targetCodeTextarea');
  getFileContents(targetUrl, true)
}

function getFileContents(url, target=false){
  fetch(url)
  .then(response => {
    if (!response.ok) {
      throw new Error(`Network response was not ok: ${response.statusText}`);
    }
    return response.json();
  })
  .then(data => {
    // The 'content' field in the response contains the base64-encoded content of the file.
    const fileContent = atob(data.content);
    // console.log(fileContent);
    if (target == false){
      baseFileContent = fileContent;
      codeTextarea.value = baseFileContent;
      // hljs.highlightBlock(codeTextarea);
    }
    else{
      targetFileContent = fileContent;
      targetCodeTextarea.value = targetFileContent;
    }
  })
  .catch(error => {
    console.error('Error fetching file content:', error);
  });
}

// // usage example
// https://github.com/Hhyemin/suppression-test-python-mypy
// 19b9ff4
// bb01e91
// src/compare/find_max.py