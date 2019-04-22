const notificationOptions = {
    time: {
        type: 'basic',
        title: 'Please hold on!',
        message: 'Highlighting process is taking more time than expected',
        iconUrl: 'https://image.flaticon.com/icons/svg/1571/1571668.svg'
    },
    error: {
        type: 'basic',
        title: 'Highlighting fails!',
        message: 'Please try again later',
        iconUrl: 'https://image.flaticon.com/icons/svg/1586/1586270.svg'
    },
    emailNotFound : {
        type: 'basic',
        title: 'Can\'t find email here!',
        message: 'Processing all web-page instead...',
        iconUrl: 'https://image.flaticon.com/icons/svg/1586/1586270.svg'
    }
};

chrome.browserAction.onClicked.addListener(function (tab) {
    const file = "/js/highlight.js";

    chrome.tabs.executeScript({file});

    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        console.log(sender.tab ?
            "from a content script:" + sender.tab.url :
            "from the extension");
        if (request.method === 'showNotification') {
            const options = notificationOptions[request.options.type];
            if (!options) return;
            chrome.notifications.create(options);
        }
    });
});
