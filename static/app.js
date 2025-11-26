function onScanSuccess(decodedText, decodedResult) {
  const resultDiv = document.getElementById('scan-result');

  // Clear previous message and styles immediately on new scan


  // Send scanned QR code to the backend for attendance marking
  fetch('/scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ barcode: decodedText })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
         // Clear "Scanning..." message before showing the response
        resultDiv.innerText = "";
        resultDiv.innerText = data.message;
        resultDiv.style.color = "green";
        resultDiv.style.border = "2px solid #22aa22";
        resultDiv.style.background = "#e8ffe8";
      } else {
        if (data.message.toLowerCase().includes("already")) {
          // Show user name from returned message for 1 second then clear
          resultDiv.innerText = data.message; // expected to include name
          resultDiv.style.color = "#138496";           // teal text
          resultDiv.style.border = "2px solid #17a2b8"; // bright teal border
          resultDiv.style.background = "#d1ecf1";      // light teal background
          
          setTimeout(() => {
            resultDiv.innerText = "";
            resultDiv.style.border = "none";
            resultDiv.style.background = "transparent";
          }, 1000); // Clear after 1 second
          
        } else {
          resultDiv.innerText = "Error: " + data.message;
          resultDiv.style.color = "red";
          resultDiv.style.border = "2px solid #cc2222";
          resultDiv.style.background = "#ffe8e8";
        }
      }
    })
    .catch(err => {
      resultDiv.innerText = "Server error. Try again.";
      resultDiv.style.color = "grey";
      resultDiv.style.background = "#fff8";
      resultDiv.style.border = "2px solid #aaaa";
    });
}

// Start the QR code scanner on page load
let html5QrcodeScanner = new Html5QrcodeScanner(
  "reader", { fps: 10, qrbox: 250 }, false);
html5QrcodeScanner.render(onScanSuccess);
