const highlight = `
    const random = () => Math.floor(Math.random()*2);
    const regex = /[^а-яa-z0-9]/gi;
    
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
        
        const instance = new Mark(node);
        random() % 2 === 0 ? instance.mark(text, node) : null;   
    }
    
    walkDOM(document.body, highlightFunc);
`;

chrome.browserAction.onClicked.addListener(function (tab) {
    console.log("Click event");
    chrome.tabs.executeScript({code: highlight}, (res) => console.log);
});
