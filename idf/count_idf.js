const path = require("path");
const fs = require('fs');

const fileName = "1grams-3.txt";
const idf = {};
let linesParsed = 0;

const file = fs.readFileSync(path.join(__dirname, fileName), "utf-8");
const lines = file.split("\n");
console.log("Parsing started!");

lines.forEach(line => {
    const [tf, word] = line.split("\t");
    if (!word || !tf) return;

    idf[word.toLowerCase()] = tf;
});

console.log("Parsing finished!");
fs.writeFileSync(path.join(__dirname, "../plugin/idf.js"), "const idf = " + JSON.stringify(idf), "utf-8");
console.log("Idf was saved to json file");