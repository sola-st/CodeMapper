let jsonData = [];
let currentIndex = 0;

function readFile() {
  const fileInput = document.getElementById('fileInput');
  const file = fileInput.files[0];

  if (file) {
      const reader = new FileReader();

      reader.onload = function (e) {
          jsonData = JSON.parse(e.target.result);
          displayCurrentItem();
          document.getElementById('changeOperation').style.visibility = "visible";
          document.getElementById('category').style.visibility = "visible";
          document.getElementById('mark').style.visibility = "visible";
          document.getElementById('count').style.visibility = "visible";
      };

      reader.readAsText(file);
  } else {
      window.alert('No file selected.');
  }
}

function displayCurrentItem() {
  if (jsonData.length > 0) {
      const currentItem = jsonData[currentIndex];
      document.getElementById('repo').value = currentItem.url;
      document.getElementById('sourceCommit').value = currentItem.source_commit;
      document.getElementById('targetCommit').value = currentItem.target_commit;
      document.getElementById('sourceFilePath').value = currentItem.source_file;
      document.getElementById('targetFilePath').value = currentItem.target_file;
      start_at_1 = currentIndex +1;
      document.getElementById('dataIdx').innerText = "#" + start_at_1;
      document.getElementById('distance').innerText = currentItem.kind;
  } else {
      jsonContentDiv.innerText = 'No data available.';
  }
}

function showNext() {
  document.getElementById('codeTextarea').innerText = "";
  document.getElementById('targetCodeTextarea').innerText = "";
  document.getElementById('operationSelect').value = "change";
  document.getElementById('mark').value = "";
  document.getElementById('categorySelect').value = "single identifier/word";
  
  if (jsonData.length > 0) {
      currentIndex = (currentIndex + 1) % jsonData.length;
      displayCurrentItem();
  }
}

