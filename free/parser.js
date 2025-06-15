const fs = require('fs');
const acorn = require('acorn');
const path = require('path');

const filePath = process.argv[2];

if (!filePath) {
    console.error("Error: No file path provided.");
    process.exit(1);
}

const sourceCode = fs.readFileSync(filePath, 'utf-8');
const sourceLines = sourceCode.split('\n');
const entries = [];
const processedLines = new Set();

function getCodeSnippet(node) {
    const startLine = node.loc.start.line - 1;
    const endLine = node.loc.end.line;
    return sourceLines.slice(startLine, endLine).join('\n').trim();
}

function addEntry(node, nodeType, name = "") {
    if (!node.loc) return;
    const start = node.loc.start.line;
    const end = node.loc.end.line;

    if (Array.from(processedLines).some(line => line >= start && line <= end)) {
        return;
    }

    if (!name && node.id && node.id.name) {
        name = node.id.name;
    }

    entries.push({
        type: nodeType,
        name: name,
        start_line: start,
        end_line: end,
        code: getCodeSnippet(node),
        file_path: path.resolve(filePath)
    });

    for (let i = start; i <= end; i++) {
        processedLines.add(i);
    }
}

try {
    const ast = acorn.parse(sourceCode, {
        ecmaVersion: 'latest', // 최신 JS 문법 지원
        sourceType: 'module',
        locations: true
    });

    ast.body.forEach(node => {
        switch (node.type) {
            case 'FunctionDeclaration':
                addEntry(node, 'function');
                break;
            case 'ClassDeclaration':
                addEntry(node, 'class');
                break;
            case 'ImportDeclaration':
                addEntry(node, 'module');
                break;
            case 'ExportNamedDeclaration':
            case 'ExportDefaultDeclaration':
                if (node.declaration) {
                    const decl = node.declaration;
                    const type = decl.type.replace('Declaration', '').toLowerCase();
                    addEntry(decl, type);
                } else {
                    addEntry(node, 'export');
                }
                break;
        }
    });

    ast.body.forEach(node => {
        if (node.loc && !processedLines.has(node.loc.start.line)) {
            addEntry(node, 'script');
        }
    });

    entries.sort((a, b) => a.start_line - b.start_line);

    // 최종 결과를 JSON 문자열로 출력
    console.log(JSON.stringify(entries, null, 2));

} catch (error) {
    console.error(`Error parsing ${filePath}: ${error.message}`);
    process.exit(1);
}