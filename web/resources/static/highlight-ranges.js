let tempSource = [];
let tempTarget = [];
let memoryStack = [];

function getCursorPosition(lines, offset, mark) {
    var line = 1;
    var character = 1;
    var plus = 0; // count the added missing "\n"s

    var line_counts = lines.length + 1;
    for (var i = 0; i < line_counts; i++) {
        var lineLength = lines[i].length + 1; 
        if (offset < lineLength) {
            character = offset;
            break;
        } 
        else if (mark == "start") {
            offset+=1; // add the missed length of "\n"
            plus+=1;
        }
        
        offset -= lineLength;
        line++;
    }
        
    return { line: line, character: character, plus: plus };
}

function getSelectedTextPosition(highlightedDiv) {
    var selection = getSelectedText(highlightedDiv);
    if (selection.text !== '') {
        var text = highlightedDiv.innerText;
        var lines = text.split('\n');

        var startPosition = getCursorPosition(lines, selection.startOffset, "start");
        selection.endOffset +=startPosition.plus; // real endOffset
        var endPosition = getCursorPosition(lines, selection.endOffset, "end");

        console.log("RR: ", startPosition.line, startPosition.character, endPosition.line, endPosition.character);
        const data = [startPosition.line, startPosition.character, endPosition.line, endPosition.character].toString();
        
        var id = highlightedDiv.id;
        if (id == "codeTextarea") {
            tempSource.push(data);
        } else if (id == "targetCodeTextarea"){
            tempTarget.push(data);
        }
    }
}

function highlightSelectedText(highlightedDiv) {
    var selection = getSelectedText(highlightedDiv);
    if (selection.text !== '') {
        // Remove existing highlights within the specific div
        var existingHighlights = highlightedDiv.querySelectorAll(".highlight");
        existingHighlights.forEach(function (highlight) {
            highlight.classList.remove("highlight");
        });

        // Apply new highlight
        var range = window.getSelection().getRangeAt(0);
        const hl = new Highlight();
        hl.add(range);

        var id = highlightedDiv.id;
        if (id == "codeTextarea") {
            CSS.highlights.set("source", hl);
        } else if (id == "targetCodeTextarea"){
            CSS.highlights.set("target", hl);
        }

        // console.log("Selected Text: ", selection.text);
        getSelectedTextPosition(highlightedDiv);
    }
}

function getSelectedText(highlightedDiv) {
    var selectedText = "";
    var startOffset = -1;
    var endOffset = -1;

    var selection = window.getSelection();
    if (selection) {
        selectedText = selection.toString();
        var range = selection.getRangeAt(0);

        var preSelectionRange = document.createRange();
        preSelectionRange.selectNodeContents(highlightedDiv);
        preSelectionRange.setEnd(range.startContainer, range.startOffset);

        // + 1 to let startOffset number starts at 1. 
        startOffset = preSelectionRange.toString().length + 1;
        // [startOffset, endOffset]
        // let endOffset includes the end character
        endOffset = startOffset + selectedText.toString().length - 1; 
    } else if (document.selection && document.selection.type != "Control") {
        var range = document.selection.createRange();
        selectedText = range.text;
        startOffset = 1; 
        endOffset = selectedText.length;
    }

    return { text: selectedText, startOffset: startOffset, endOffset: endOffset };
}

document.querySelectorAll(".highlightedDiv").forEach(function (highlightedDiv) {
    highlightedDiv.addEventListener("mouseup", function () {
        highlightSelectedText(highlightedDiv);
    });
});

function pushToMemory() {
    var desiredSource = tempSource.pop();
    var desiredTarget = tempTarget.pop();
    var formattedDesiredTarget = "["+desiredTarget+"]";
    if (desiredTarget == undefined){
        formattedDesiredTarget = null;
    }
    console.log('Temporary data pairs:', [desiredSource, desiredTarget]);
    memoryStack.push({
        url: document.getElementById('repo').value,
        mapping: {
            source_file: document.getElementById('sourceFilePath').value,
            target_file: document.getElementById('targetFilePath').value,
            source_commit: document.getElementById('sourceCommit').value,
            target_commit: document.getElementById('targetCommit').value,
            source_range: "["+desiredSource+"]",
            target_range: formattedDesiredTarget,
            change_operation: document.getElementById('operationSelect').value,
            kind: document.getElementById('distance').innerText,
            category: document.getElementById("categorySelect").value,
            detail: document.getElementById('mark').value
        }
    });
    removeHighlights("codeTextarea");
    removeHighlights("targetCodeTextarea");
    // update the number of different categories.
    var kind_value = document.getElementById('distance').innerText;
    var category_value = document.getElementById('categorySelect').value;
    var table_cell_id;
    if(kind_value == "neighboring"){
        table_cell_id = "N" + category_value;
    }else{ // distance
        table_cell_id = "K" + category_value;
    }
    var currentValue = document.getElementById(table_cell_id).innerText;
    document.getElementById(table_cell_id).innerText = parseInt(currentValue) + 1;
  }

function removeHighlights(id) {
  var allHighlights = document.getElementById(id).querySelectorAll(".highlight");
  allHighlights.forEach(function (highlight) {
      highlight.classList.remove("highlight");
  });
}

function saveAnnotations() {
    // download the annotations as a JSON file
    var jsonString = JSON.stringify(memoryStack, null, 2);
    var blob = new Blob([jsonString], { type: "application/json" });
    var url = URL.createObjectURL(blob);

    var a = document.createElement("a");
    a.href = url;
    a.download = "annotations.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}