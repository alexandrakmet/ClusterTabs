chrome.action.onClicked.addListener((tab) => {
    chrome.tabs.create({
        url: chrome.runtime.getURL('popup/popup.html'),
        active: true
    });
});