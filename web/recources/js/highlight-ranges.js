function highlight(color) {
  const selection = window.getSelection();
  const range = selection.getRangeAt(0);

  // Check if the selection is already highlighted
  const isHighlighted = range.commonAncestorContainer.parentElement.style.backgroundColor === color;

  // Remove highlighting if the same text is reselected
  if (isHighlighted) {
    const parentElement = range.commonAncestorContainer.parentElement;
    parentElement.outerHTML = parentElement.innerHTML;
    return;
  }

  // Create a new span and apply highlighting
  const span = document.createElement('span');
  span.style.backgroundColor = color;

  // Save the start and end locations of the selection
  const startOffset = range.startOffset;
  const endOffset = range.endOffset;

  span.dataset.startOffset = startOffset;
  span.dataset.endOffset = endOffset;

  // Calculate line and character numbers
  const textContent = range.commonAncestorContainer.textContent;

  const startLine = textContent.substr(0, startOffset).split('\n').length;
  const endLine = textContent.substr(0, endOffset).split('\n').length;
  const startCharacter = startOffset - textContent.lastIndexOf('\n', startOffset - 1);
  const endCharacter = endOffset - textContent.lastIndexOf('\n', endOffset - 1);

  span.dataset.startLine = startLine;
  span.dataset.startCharacter = startCharacter;
  span.dataset.endLine = endLine;
  span.dataset.endCharacter = endCharacter;

  range.surroundContents(span);
}


function saveAnnotations() {
  const highlightedSpans = document.querySelectorAll('.highlightedDiv span');
  
  if (highlightedSpans.length === 0) {
    console.error('No highlighted texts to save.');
    return;
  }

  const annotations = [];
  const lastTwoSpans = Array.from(highlightedSpans).slice(-2);

  lastTwoSpans.forEach(span => {
    const text = span.innerText;
    const startLine = span.dataset.startLine;
    const startCharacter = span.dataset.startCharacter;
    const endLine = span.dataset.endLine;
    const endCharacter = span.dataset.endCharacter;

    annotations.push({
      range: text,
      position: {
        startLine,
        startCharacter,
        endLine,
        endCharacter
      }
    });
  });

  const jsonContent = JSON.stringify(annotations, null, 2);

  // Save the JSON file to a specified local folder (modify the path accordingly)
  const blob = new Blob([jsonContent], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'annotations.json';
  a.click();
}
