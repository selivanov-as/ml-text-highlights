const highlight = `
    var API_URL = "http://localhost:5000/tf-idf";
    var regex = /[^a-яё0-9]/gi;
    var tf = {};
    var words = [];
    var punctuationSymbols = [":", ";", ".", ",", "-", "–", "—", "‒", "_", "(", ")", "{", "}", "[", "]", "!", "'", "+", "="];
    
    var walkDOM = (node, func) => {
        func(node);
        node = node.firstChild;
        while(node) {
            walkDOM(node, func);
            node = node.nextSibling;
        }
    
    };
    
    var highlightFunc = (node) => {
        if (node.nodeName !== '#text') return;
        
        var text = node.textContent;
        text = text.replace(regex, ' ');
        text = text.split(' ');

        if (!text.length) return; 
        
        text.forEach(word => word.length ? words.push(word) : null);
    }
    
    walkDOM(document.body, highlightFunc);
    axios.post(API_URL, words).then(result => {
        var instance = new Mark(document.body);
        console.log(result.data);
        result.data.slice(0, (result.data.length * 0.3) >> 0).forEach(elem => {
            instance.mark(elem.word, 
                         {"accuracy": {
                            "value": "exactly",
                            "limiters": [",", ".", "-", ":"]
                         }, 
                         acrossElements: true});
        });
        /*Object.keys(result.data).forEach(word => {
            if (result.data[word] >= 0.25) instance.mark(word, {accuracy: "exactly", acrossElements: true});
        });*/
    });
`;

chrome.browserAction.onClicked.addListener(function (tab) {
    console.log("Click event");
    chrome.tabs.executeScript({code: highlight}, (res) => console.log); //ToDo: Reuse code from Hightlight.js
});
