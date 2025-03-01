const API_URL = "http://localhost:5000/api/predict"; 
let lastCheckedUrl = "";

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url && 
        tab.url.startsWith("http") && tab.url !== lastCheckedUrl) {
        lastCheckedUrl = tab.url;
        analyzeUrl(tab.url);
    }
});

async function analyzeUrl(url) {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });
        
        if (!response.ok) {
            throw new Error(`API returned ${response.status}`);
        }
        
        const data = await response.json();
        if (data.error) {
            console.error("API Error:", data.error);
            return;
        }
        
        const { prediction, confidence } = data;
        chrome.storage.local.set({ lastCheck: { url, prediction, confidence } });
        
        if (prediction === 1) {
            chrome.action.setBadgeText({ text: "⚠️" });
            chrome.action.setBadgeBackgroundColor({ color: "#d9534f" });
        } else {
            chrome.action.setBadgeText({ text: "" });
        }
    } catch (error) {
        console.error("Failed to fetch API:", error);
        chrome.storage.local.set({ 
            lastCheck: { 
                url, 
                error: true, 
                errorMessage: error.message 
            } 
        });
    }
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getStatus") {
        chrome.storage.local.get("lastCheck", (result) => {
            sendResponse(result.lastCheck);
        });
        return true;
    }
    
    if (request.action === "forceCheck" && request.url) {
        analyzeUrl(request.url);
        sendResponse({ status: "checking" });
        return true;
    }
});