// Verify that the document preserves its PWA links and their local targets.
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
let pass = true;

function check(name, condition) {
  if (condition) console.log('PASS:', name);
  else {
    pass = false;
    console.error('FAIL:', name);
  }
}

const links = [
  ['manifest', 'site.webmanifest'],
  ['apple-touch-icon', 'assets/icons/icon-192.png'],
];

for (const [rel, href] of links) {
  const linkPattern = new RegExp(`<link\\s+rel=["']${rel}["']\\s+href=["']${href}["']\\s*/?>`, 'i');
  check(`${rel} link exists`, linkPattern.test(html));
  check(`${rel} target exists`, fs.existsSync(path.join(root, href)));
}

console.log(pass ? '\nALL CHECKS PASSED' : '\nSOME CHECKS FAILED');
process.exit(pass ? 0 : 1);