const fs = require('fs');

// Path to the extracted sheet2.xml (stock_core_master)
const sheetXmlPath = 'F:/PSJ/AntigravityWorkPlace/Stock/Test_02/temp_excel_extracted/xl/worksheets/sheet2.xml';
const sharedStringsPath = 'F:/PSJ/AntigravityWorkPlace/Stock/Test_02/temp_excel_extracted/xl/sharedStrings.xml';

const sheetContent = fs.readFileSync(sheetXmlPath, 'utf8');
const stringsContent = fs.readFileSync(sharedStringsPath, 'utf8');

// Parse shared strings
const siBlocks = stringsContent.split('<si>');
const sharedStrings = siBlocks.slice(1).map(block => {
    const tStart = block.indexOf('<t');
    if (tStart !== -1) {
        const tEndPos = block.indexOf('>', tStart);
        const tClose = block.indexOf('</t>', tEndPos);
        if (tClose !== -1) {
            return block.substring(tEndPos + 1, tClose);
        }
    }
    return '';
});

// Column mapping based on header (r="1")
// A: ticker (0), B: name (1), C: core_sector_top (2), D: core_sector_sub (3), E: core_desc (4), 
// F: 해자강도 (5), G: 해자DESC (6), H: moat_name (7), I: desc (8), J: 검증용desc (9)

const rows = sheetContent.match(/<row r="(\d+)".*?>(.*?)<\/row>/g);
const targetStocks = [];

rows.forEach(rowMatch => {
    const rowNum = rowMatch.match(/r="(\d+)"/)[1];
    if (rowNum === "1") return; // Skip header

    const cells = rowMatch.match(/<c r="([A-Z]+)\d+".*?>(.*?)<\/c>/g);
    const rowData = {};

    if (cells) {
        cells.forEach(cell => {
            const col = cell.match(/r="([A-Z]+)\d+"/)[1];
            const type = cell.match(/t="s"/);
            const valMatch = cell.match(/<v>(.*?)<\/v>/);
            let val = valMatch ? valMatch[1] : '';

            if (type && val !== '') {
                val = sharedStrings[parseInt(val)];
            }
            rowData[col] = val;
        });
    }

    // Check if essential fields are missing: C (sector_top), E (core_desc), F (moat_strength), H (moat_name)
    // As per TODO, "item contents not filled" should be processed.
    const isMissing = !rowData['C'] || !rowData['E'] || !rowData['F'] || !rowData['H'];

    if (isMissing) {
        targetStocks.push({
            row: rowNum,
            ticker: rowData['A'],
            name: rowData['B'],
            missingFields: [
                !rowData['C'] ? 'core_sector_top' : '',
                !rowData['D'] ? 'core_sector_sub' : '',
                !rowData['E'] ? 'core_desc' : '',
                !rowData['F'] ? 'moat_strength' : '',
                !rowData['G'] ? 'moat_desc_detail' : '',
                !rowData['H'] ? 'moat_name' : '',
                !rowData['I'] ? 'desc' : ''
            ].filter(f => f !== '')
        });
    }
});

console.log(JSON.stringify(targetStocks, null, 2));
