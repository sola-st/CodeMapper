let tempSource = [];
let tempTarget = [];
let memoryStack = [];

function getCursorPosition(element, offset) {
    var line = 1;
    var character = 1;

    var text = element.innerText;
    var lines = text.split('\n');

    for (var i = 0; i < lines.length; i++) {
        var lineLength = lines[i].length + 1; 
        if (offset <= lineLength) {
            character = offset;
            break;
        }
        offset -= lineLength;
        line++;
    }

    return { line: line, character: character };
}

function getSelectedTextPosition(highlightedDiv) {
    var selection = getSelectedText(highlightedDiv);
    if (selection.text !== '') {
        var id = highlightedDiv.id;

        const element = document.getElementById(id);
        var startPosition = getCursorPosition(element, selection.startOffset + 1);
        var endPosition = getCursorPosition(element, selection.endOffset);

        console.log("RR: ", startPosition.line, startPosition.character, endPosition.line, endPosition.character);
        
        // const data = {
        //     selectedText: selection.text,
        //     selectionRange: [startPosition.line, startPosition.character, endPosition.line, endPosition.character].toString()
        // };
        const data = [startPosition.line, startPosition.character, endPosition.line, endPosition.character].toString();

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
        var span = document.createElement("span");
        span.className = "highlight";
        // range.surroundContents(span);
        // span.style.backgroundColor = color;
        span.appendChild(range.extractContents());
        range.insertNode(span);

        console.log("Selected Text: ", selection.text);
        getSelectedTextPosition(highlightedDiv);
    }
}

function getSelectedText(highlightedDiv) {
    var selectedText = "";
    var startOffset = -1;
    var endOffset = -1;

    if (window.getSelection) {
        var selection = window.getSelection();
        selectedText = selection.toString();
        var range = selection.getRangeAt(0);

        var preSelectionRange = document.createRange();
        preSelectionRange.selectNodeContents(highlightedDiv);
        preSelectionRange.setEnd(range.startContainer, range.startOffset);
        startOffset = preSelectionRange.toString().length;

        endOffset = startOffset + range.toString().length;
    } else if (document.selection && document.selection.type != "Control") {
        var range = document.selection.createRange();
        selectedText = range.text;
        startOffset = 0; 
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
    console.log('Temporary data pairs:', [desiredSource, desiredTarget]);
    memoryStack.push({
        mapping: {
            source_range: desiredSource,
            target_range: desiredTarget
        }
    });
    removeHighlights("codeTextarea");
    removeHighlights("targetCodeTextarea");
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