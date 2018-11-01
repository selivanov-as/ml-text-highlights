//  еще одна не оч умная версия, которая находит текстовые ноды
//  и хайлйатит их, чтото ломая почти всегда

var color = "#ffff00";
var prob = 0.1;
//var tags = ["h1", "h2", "h3", "h4", "p", "a"];


var text_nodes = [];
function dfs(node) {
    for (var child = node.firstChild; child; child=child.nextSibling) {
        if (child.nodeType == 3) {
            text_nodes.push(child);
        }
        dfs(child);
    }
}

dfs(document);

//console.log(text_nodes);

for (node of text_nodes) {
    parent = node.parentNode;
    parent_tag = parent.nodeName;
    if (parent_tag == "SCRIPT") {
        continue;
    }
    var text = node.innerText || node.textContent;
    if (!text) {
        continue;
    }
    words = text.split(' ');
    var changed = false;
    for (var i = 0, length = words.length; i < length; i += 1) {
        if (Math.random() >= prob) {
            continue;
        }
        changed = true;
        words[i] = "<span style='background-color: " + color + ";'>" + words[i] + "</span>";
    }
    
    if (changed) {
        new_node = document.createElement(parent_tag);
        new_node.innerHTML = words.join(delimiter=' ');
        parent.replaceChild(new_node, node);
    }
}







/*
for (tag of tags) {
    for (node of document.getElementsByTagName(tag)) {
        
        var text = node.innerText || node.textContent;
        if (!text) {
            cnt++;
            continue;
        }
        words = text.split(' ');
        var changed = false
        for (var i = 0, length = words.length; i < length; i += 1) {
            if (Math.random() >= prob) {
                continue;
            }
            changed = true;
            words[i] = "<span style='background-color: " + color + ";'>" + words[i] + "</span>";
        }
        
        if (changed) {
        }
        new_node = document.createElement(tag)
        new_node.innerHTML = words.join(delimiter = ' ');
        parent = node.parentNode;
        parent.replaceChild(new_node, node);
    }
}
console.log('skipped ', cnt, 'nodes');*/
