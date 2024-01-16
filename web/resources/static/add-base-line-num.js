function updateLineNumbers() {
    var content = document.getElementById("codeTextarea");
    var lines = content.innerText.split('\n');

    var lineNumberContainer = document.getElementById("baseLineNumber");
    lineNumberContainer.innerHTML = '';

    var len = lines.length;
    if (lines.length > 1 && lines[-1] == "") {
        len = len - 1;
    }
    for (var i = 0; i < len; i++) {
        var lineNumber = document.createElement('div');
        lineNumber.className = 'lineNumber';
        lineNumberContainer.appendChild(lineNumber);
    }
}

updateLineNumbers();
// Update line numbers on content change
document.getElementById("codeTextarea").addEventListener("input", updateLineNumbers);