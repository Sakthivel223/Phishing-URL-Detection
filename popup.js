document.addEventListener("DOMContentLoaded", () => {
    const loadingContainer = document.getElementById("loadingContainer");
    const resultContainer = document.getElementById("resultContainer");
    const statusElement = document.getElementById("status");
    const urlElement = document.getElementById("url");
    const confidenceElement = document.getElementById("confidence");
    const retryButton = document.getElementById("retryButton");
    
    function checkCurrentUrl() {
        loadingContainer.style.display = "block";
        resultContainer.style.display = "none";
        
        chrome.runtime.sendMessage({ action: "getStatus" }, (response) => {
            loadingContainer.style.display = "none";
            resultContainer.style.display = "block";
            
            if (!response) {
                statusElement.innerText = "Error fetching data";
                return;
            }
            
            urlElement.innerText = response.url;
            confidenceElement.innerText = response.confidence.toFixed(1) + "%";
            
            if (response.prediction === 1) {
                statusElement.innerText = "⚠️ This website is PHISHING!";
                statusElement.className = "danger";
            } else {
                statusElement.innerText = "✅ Website appears SAFE";
                statusElement.className = "safe";
            }
        });
    }
    
    // Initial check
    checkCurrentUrl();
    
    // Setup retry button
    retryButton.addEventListener("click", () => {
        chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
            if (tabs[0]) {
                chrome.runtime.sendMessage({ 
                    action: "forceCheck",
                    url: tabs[0].url
                }, () => {
                    checkCurrentUrl();
                });
            }
        });
    });
});