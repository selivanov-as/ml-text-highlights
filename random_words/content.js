var prob = 0.1;

var text_nodes = [];
function dfs(node) {
    for (var child = node.firstChild; child; child=child.nextSibling) {
        if (child.nodeName === '#text') {
            text_nodes.push(child);
        }
        dfs(child);
    }
}

dfs(document.body);

for (node of text_nodes) {
    parent = node.parentNode;
    parent_tag = parent.nodeName;
    if (parent_tag == "SCRIPT" || parent_tag == "STYLE") {
        continue;
    }
    var text = node.innerText || node.textContent;
    if (text.search(/[а-яa-z0-9]/gi) < 0) {
        continue;
    }
    words = text.split(' ');
    var changed = [];
    for (var i = 0, length = words.length; i < length; i++) {
        if (Math.random() >= prob) {
            continue;
        }
        changed.push(i);
    }
    if (changed.length > 0) {
        first_node = document.createTextNode(
            words.slice(
                null, changed[0]
            ).join(delimeter=' ') +
            ((changed[0] > 0) ? ' ' : '')
        )
        parent.replaceChild(first_node, node)
        last_node = first_node.nextSibling
        for (var i = 0; i < changed.length; i++) {
            marked_node = document.createElement("mark")
            marked_node.textContent = words[changed[i]]
            parent.insertBefore(marked_node, last_node)
            text_node = document.createTextNode(
                ((changed[i] + 1 < words.length) ? ' ' : '') + 
                words.slice(
                    changed[i] + 1, changed[i + 1]
                ).join(delimiter=' ') +
                ((i + 1) < changed.length ? ' ' : '')
            )
            parent.insertBefore(text_node, last_node)
        }
    }
}
