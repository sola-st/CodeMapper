function startProject() {
    console.log('startProject function called');
    // Make an AJAX request to start the Python project
    fetch('/start_project', {
        method: 'POST'
    })
    .then(response => response.json())  // Corrected line
    .then(data => {
        console.log(data);  // This line logs the data
        // Display the results on the webpage
        document.getElementById('result').innerText = data.output;
    })
    .catch(error => {
        console.error('Fetch error:', error);
    });
}
