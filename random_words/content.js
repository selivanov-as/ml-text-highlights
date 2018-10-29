// не оч умная версия, которая находит только теги из фиксированного списка,
// и тупо хайлйатит их, возможно чтото ломая

var color = "#ffff00";
var prob = 0.1;
var cnt = 0;
var tags = ["h1", "h2", "h3", "h4", "p", "a"];
for (tag of tags) {
    for (node of document.getElementsByTagName(tag)) {
        
        var text = node.innerText || node.textContent;
        if (!text) { // || node.hasChildNodes(
            cnt++;
            continue;
        }
        words = text.split(' ');
        for (var i = 0, length = words.length; i < length; i += 1) {
            if (Math.random() >= prob) {
                continue;
            }
            words[i] = "<span style='background-color: " + color + ";'>" + words[i] + "</span>";
            node.innerHTML = words.join(delimiter = ' ');
        }
    }
}
console.log('skipped ', cnt, 'nodes');
