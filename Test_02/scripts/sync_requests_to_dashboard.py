import re
import json
import os
from pathlib import Path

class RequestsParser:
    def __init__(self, requests_file_path):
        self.requests_file_path = requests_file_path
        self.content = ""
        self.requests = []

    def read_file(self):
        with open(self.requests_file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def parse(self):
        self.read_file()
        
        # 1. Parse Summary Table for ID, Title, Status
        # Use ^ anchor and re.MULTILINE to ensure we match start of line.
        # Use [ \t]* instead of \s* to avoid matching newlines in spacing.
        summary_pattern = r'^\|\s*(REQ-\d+)\s*\|\s*([^|\n]*?)\s*\|\s*([^|\n]*?)\s*\|'
        matches = re.findall(summary_pattern, self.content, flags=re.MULTILINE)
        
        summary_map = {}
        for req_id, title, status in matches:
            if req_id == 'REQ-ID': continue # Skip header
            summary_map[req_id] = {
                'id': req_id,
                'title': title.strip(),
                'status': status.strip()
            }

        # 2. Parse Detailed Sections
        # Split by "### REQ-" to handle each section
        sections = re.split(r'###\s+(REQ-\d+):', self.content)
        
        # sections[0] is preamble. Then we have pairs of (id, content)
        for i in range(1, len(sections), 2):
            req_id = sections[i]
            section_content = sections[i+1]
            
            if req_id not in summary_map:
                continue
                
            req_data = summary_map[req_id]
            
            # Parse Details
            req_data['stage'] = self._extract_field(section_content, '상태', '진행') # Fallback to summary status if needed, but summary table status is '진행', '완료' etc.
            # Actually, the summary table status is the source of truth for high level status.
            # Let's map Summary Status to Dashboard Status
            # '진행' -> '개발중', '완료' -> '완료', '대기' -> '미착수'
            
            # Parse Owner/Due/Stage from detailed table logic if present, 
            # OR generic extraction. 
            # In REQUESTS.md, specific fields like Owner/Due might NOT be in a standard table for all.
            # But let's try to parse the "Table" right after the header if exists.
            
            # Extract Checklist
            req_data['checklist'] = self._extract_checklist(section_content)
            
            # Extract Programs (Related Files)
            req_data['programs'] = self._extract_related_files(section_content)
            
            # Default values for missing fields to avoid breaking dashboard
            req_data['owner'] = 'TBD' # Placeholder
            req_data['due'] = '-'
            req_data['nextAction'] = '-'
            
            # Attempt to find "담당" or "Owner" or imply from context? 
            # Currently REQUESTS.md doesn't explicitly have "Owner" column in details usually.
            # We will use hardcoded mapping or heuristics if needed, but for now default to generic.
            
            self.requests.append(req_data)

        # Sort by ID
        self.requests.sort(key=lambda x: x['id'])
        return self.requests

    def _extract_field(self, content, field_name, default_val):
        # Try to find "| field_name | value |"
        pattern = fr'\|\s*{field_name}\s*\|\s*(.*?)\s*\|'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return default_val

    def _extract_checklist(self, content):
        items = []
        # Find numeric list "1. item" or "- [ ] item" under "#### 요구사항" or just generic
        # Look for "#### 요구사항" block
        reqs_match = re.search(r'#### 요구사항\s*(.*?)\s*(?:####|$)', content, re.DOTALL)
        if reqs_match:
            req_text = reqs_match.group(1)
            # Parse numbered list
            lines = req_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line: continue
                # Match "1. Content"
                m = re.match(r'\d+\.\s*(.*)', line)
                if m:
                    # Check if it's considered "Done"? 
                    # In REQUESTS.md, requirements are usually static text.
                    # We might need to look for "- [x]" syntax if used, or default to boolean based on global status.
                    # If status is '완료', list items are true.
                    is_done = False # Dynamic parsing is hard without checkboxes
                    label = m.group(1)
                    items.append({'label': label, 'done': is_done})
        
        # Also look for actual checklist syntax if present (e.g. in updates)
        checkbox_matches = re.findall(r'- \[(x| )\] (.*)', content, re.IGNORECASE)
        for mark, label in checkbox_matches:
            items.append({'label': label.strip(), 'done': mark.lower() == 'x'})

        # If we found explicit checkboxes, prefer those? 
        # Actually mixed is fine.
        return items

    def _extract_related_files(self, content):
        programs = []
        files_match = re.search(r'#### 관련 파일\s*(.*?)\s*(?:####|$)', content, re.DOTALL)
        if files_match:
            files_text = files_match.group(1)
            # Find list items
            lines = files_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                # - `path/to/file`
                m = re.match(r'-\s*`?(.*?)`?$', line)
                if m:
                    path = m.group(1).strip('`')
                    if path:
                        programs.append({
                            'name': os.path.basename(path),
                            'path': path,
                            'description': 'Related file'
                        })
        return programs

class DashboardDataGenerator:
    def __init__(self, output_path):
        self.output_path = output_path

    def generate(self, requests):
        js_content = "(function () {\n    window.PROJECT_STATUS_ITEMS = [\n"
        
        for req in requests:
            # Map Status
            status = req['status']
            
            # Infer logic for done checklist if status is completed
            if status == '완료':
                for item in req['checklist']:
                    item['done'] = True
            
            req_obj = {
                'id': req['id'],
                'title': f"{req['id']} {req['title']}", # Combine ID and Title
                'status': status,
                'stage': status, # Default stage to status
                'owner': req.get('owner', 'TBD'),
                'due': req.get('due', '-'),
                'programs': req.get('programs', []),
                'checklist': req.get('checklist', []),
                'nextAction': req.get('nextAction', '-')
            }
            
            json_str = json.dumps(req_obj, ensure_ascii=False, indent=12)
            # Indent fix for pretty printing inside the array
            json_str = json_str.strip() 
            js_content += "        " + json_str + ",\n"

        js_content = js_content.rstrip(",\n") + "\n"
        js_content += "    ];\n})();\n"
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"Successfully generated {self.output_path}")

def main():
    base_dir = Path(__file__).parent.parent
    requests_path = base_dir / "REQUESTS.md"
    output_path = base_dir / "dashboard/js/project_status_data.js"
    
    print(f"Reading from: {requests_path}")
    print(f"Writing to: {output_path}")
    
    parser = RequestsParser(requests_path)
    requests = parser.parse()
    
    generator = DashboardDataGenerator(output_path)
    generator.generate(requests)

if __name__ == "__main__":
    main()
