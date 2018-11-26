const highlight = `
    const regex = /[^a-яё0-9]/gi;
    const tf = {};
    let wordsAmount = 0;
    
    const walkDOM = (node, func) => {
        func(node);
        node = node.firstChild;
        while(node) {
            walkDOM(node, func);
            node = node.nextSibling;
        }
    
    };
    
    const highlightFunc = (node) => {
        if (node.nodeName !== '#text') return;
        
        var text = node.textContent;
        text = text.replace(regex, ' ');
        text = text.split(' ');

        if (!text.length) return; 
        
        text.forEach(word => {
            if (!tf[word.toLowerCase()]) {
                tf[word.toLowerCase()] = [1, [node]];
                wordsAmount++;
            } else {
                tf[word.toLowerCase()][0]++;
                tf[word.toLowerCase()][1].push(node)
            }
        });
    }
    
    walkDOM(document.body, highlightFunc);
    const multiplier = 1000;
    const instance = new Mark(document);
    Object.keys(tf).forEach(term => {
        const term_idf = idf[term] ? idf[term] : 0;
        const tf_idf = (tf[term][0] / wordsAmount * multiplier) / term_idf;
        if (tf_idf >= 0.3) {
            tf[term][1].forEach(context => instance.mark(term, {accuracy: "exactly"}))
        }
    });
    
`;

const makeHTTPRequest = `
    axios.get('http://localhost:3000/').then(function(response) {
        console.log("response", response);
    });
`;

chrome.browserAction.onClicked.addListener(function (tab) {
    console.log("Click event");
    chrome.tabs.executeScript({code: makeHTTPRequest}, (res) => console.log); //ToDo: Reuse code from Hightlight.js
});
