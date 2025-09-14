const fs = require('fs');
const acorn = require('acorn');
const path = require('path');

const [,, inputDir, outputDir] = process.argv;
if (!inputDir || !outputDir) {
  console.error('Usage: node parser.js <input_directory> <output_directory>');
  process.exit(1);
}

try {
  if (!fs.statSync(inputDir).isDirectory()) {
    console.error(`Error: Input path is not a directory. Received: ${inputDir}`);
    process.exit(1);
  }
} catch (e) {
  console.error(`Error: Invalid input path. Could not access: ${inputDir}`);
  process.exit(1);
}

function walkDir(dir, callback) {
  fs.readdirSync(dir, { withFileTypes: true }).forEach(dirent => {
    const fullPath = path.join(dir, dirent.name);
    if (dirent.isDirectory()) {
      if (dirent.name !== '.git') {
        walkDir(fullPath, callback);
      }
    } else if (dirent.isFile() && dirent.name.endsWith('.js')) {
      callback(fullPath);
    }
  });
}

function parseFile(filePath) {
  const sourceCode = fs.readFileSync(filePath, 'utf-8');
  if (!sourceCode.trim()) {
      return [];
  }
  const sourceLines = sourceCode.split('\n');
  const entries = [];
  const processedLines = new Set();

  function getCodeSnippet(node) {
    const startLine = node.loc.start.line - 1;
    const endLine = node.loc.end.line;
    return sourceLines.slice(startLine, endLine).join('\n').trim();
  }

  function addEntry(node, type, name = '') {
    if (!node.loc) return;
    const start = node.loc.start.line;
    const end = node.loc.end.line;

    // 중복 추가 방지
    for (let i = start; i <= end; i++) {
      if (processedLines.has(i)) return;
    }

    if (!name && node.id && node.id.name) name = node.id.name;
    entries.push({ type, name, start_line: start, end_line: end, code: getCodeSnippet(node), file_path: filePath });

    for (let i = start; i <= end; i++) processedLines.add(i);
  }

  try {
    const ast = acorn.parse(sourceCode, { ecmaVersion: 'latest', sourceType: 'module', locations: true });

    ast.body.forEach(node => {
      switch (node.type) {
        case 'FunctionDeclaration': addEntry(node, 'function'); break;
        case 'ClassDeclaration':    addEntry(node, 'class');    break;
        case 'ImportDeclaration':   addEntry(node, 'module');   break;
        case 'ExportNamedDeclaration':
        case 'ExportDefaultDeclaration':
          if (node.declaration) {
            const decl = node.declaration;
            const t = decl.type.replace('Declaration','').toLowerCase();
            addEntry(decl, t);
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

    entries.sort((a,b) => a.start_line - b.start_line);
  } catch (err) {
    console.error(`[Parsing Error] Failed to parse ${filePath}: ${err.message}`);
    return null;
  }
  return entries;
}

// --- 메인 처리 로직 ---
walkDir(inputDir, jsFile => {
  const rel = path.relative(inputDir, jsFile);
  const outFile = path.join(outputDir, rel.replace(/\.js$/, '.json'));

  fs.mkdirSync(path.dirname(outFile), { recursive: true });

  const data = parseFile(jsFile);

  if (data) {
    if (data.length > 0) {
        fs.writeFileSync(outFile, JSON.stringify(data, null, 2), 'utf-8');
        console.log(`[OK] ${outFile}`);
    }
  } else {
    console.error(`[FAIL] ${jsFile}`);
  }
});

console.log('JavaScript parsing complete for directory:', inputDir);