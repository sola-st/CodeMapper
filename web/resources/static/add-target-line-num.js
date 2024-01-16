function updateLineNumbersTarget() {
    var content = document.getElementById("targetCodeTextarea");
    var lines = content.innerText.split('\n');

    var lineNumberContainer = document.getElementById("targetLineNumber");
    lineNumberContainer.innerHTML = '';

    for (var i = 0; i < lines.length; i++) {
        var lineNumber = document.createElement('div');
        lineNumber.className = 'lineNumber';
        lineNumberContainer.appendChild(lineNumber);
    }
}

updateLineNumbersTarget();
document.getElementById("targetCodeTextarea").addEventListener("input", updateLineNumbersTarget);