const fs = require('fs');
const content = fs.readFileSync('F:/PSJ/AntigravityWorkPlace/Stock/Test_02/temp_excel_extracted/xl/sharedStrings.xml', 'utf8');

// Simple regex to find all <si> blocks
const siBlocks = content.split('<si>');
// Index 0 is before the first <si>, so indices are 1-based in this split, 
// but Excel indices are 0-based relative to the sst count.
// Wait, split('<si>') will give:
// [0]: prefix
// [1]: contents of first <si> ...
// So siBlocks[index + 1] should be the string at index.

const targetIndices = [200, 201, 0, 202, 1, 203, 2, 455, 3, 880, 4, 456, 457, 458, 459, 878, 460, 461, 465, 464, 478, 479, 204, 205, 462, 463];

targetIndices.forEach(idx => {
    const block = siBlocks[idx + 1];
    if (block) {
        // Extract content between <t> and </t>
        // Use a simple indexOf because regex might be slow on large strings
        const tStart = block.indexOf('<t');
        if (tStart !== -1) {
            const tEndPos = block.indexOf('>', tStart);
            const tClose = block.indexOf('</t>', tEndPos);
            if (tClose !== -1) {
                const text = block.substring(tEndPos + 1, tClose);
                console.log(`Index ${idx}: ${text}`);
            }
        }
    }
});
