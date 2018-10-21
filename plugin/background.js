const highlight = `
    var words = [];

    var walkDOM = function (node, func) {
        func(node);
        node = node.firstChild;
        while(node) {
            walkDOM(node, func);
            node = node.nextSibling;
        }
    
    };
    
    walkDOM(document.body, function (node) {
    
        if (node.nodeName === '#text') {
            var text = node.textContent;
    
            text = text.replace(/[^A-Za-z]/g, ' ');
    
            text = text.split(' ');
    
            if (text.length) {
    
                for (var i = 0, length = text.length; i < length; i += 1) {
                    var matched = false,
                        word = text[i];
    
                    for (var j = 0, numberOfWords = words.length; j < numberOfWords; j += 1) {
                        if (words[j][0] === word) {
                            matched = true;
                            words[j][1] += 1;
                        }
                    }
    
                    if (!matched) {
                        words.push([word, 1]);
                    }
    
                }
            }
        }
    });
    
    //code from https://stackoverflow.com/a/14105425/8048608
    
    var context = document.querySelector("body");
    var instance = new Mark(context);
    
    const random = () => Math.floor(Math.random()*2)
    
    for (var i = 0, length = words.length; i < length; i += 1) {
        random() % 2 === 0 ? instance.mark(words[i][0]) : null;
    }
`;

chrome.browserAction.onClicked.addListener(function (tab) {
    console.log("Click event");
    chrome.tabs.executeScript({code: highlight}, (res) => console.log);
});