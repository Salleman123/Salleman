# core/export_engine.py
"""
Export engine for sending lineup data to vMix or files
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class ExportEngine:
    """
    Handles data export to vMix inputs or files based on mappings
    """
    
    def __init__(self, vmix_client, lineup_state):
        """
        Args:
            vmix_client: VmixClient instance for vMix communication
            lineup_state: LineupState instance with current data
        """
        self.vmix = vmix_client
        self.lineup = lineup_state
    
    def export_all(self, mappings: List[Dict]) -> List[Dict]:
        """
        Export all enabled mappings
        
        Args:
            mappings: List of export mapping dicts from config
            
        Returns:
            List of result dicts with success/failure info
        """
        results = []
        
        for mapping in mappings:
            if not mapping.get('enabled', True):
                continue
            
            try:
                result = self._export_single(mapping)
                results.append({
                    'id': mapping.get('id', 'unknown'),
                    'data_source': mapping.get('data_source', ''),
                    'success': True,
                    'message': result
                })
            except Exception as e:
                results.append({
                    'id': mapping.get('id', 'unknown'),
                    'data_source': mapping.get('data_source', ''),
                    'success': False,
                    'message': str(e)
                })
        
        return results
    
    def _export_single(self, mapping: Dict) -> str:
        """
        Export single mapping
        
        Args:
            mapping: Export mapping dict
            
        Returns:
            Success message string
            
        Raises:
            ValueError: If data source not found or export fails
        """
        # Get data from lineup state
        data = self.lineup.get_exportable_data()
        data_source_key = mapping.get('data_source')
        
        if data_source_key not in data:
            raise ValueError(f"Unknown data source: {data_source_key}")
        
        source_data = data[data_source_key]
        
        if not source_data:
            raise ValueError(f"No data available for {data_source_key}")
        
        # Export based on type
        export_type = mapping.get('export_type', 'vmix')
        
        if export_type == 'vmix':
            return self._export_to_vmix(
                source_data,
                mapping.get('destination', ''),
                mapping.get('field', '')
            )
        elif export_type == 'file':
            return self._export_to_file(
                source_data,
                mapping.get('destination', ''),
                mapping.get('format', 'text')
            )
        else:
            raise ValueError(f"Unknown export type: {export_type}")
    
    def _export_to_vmix(self, data: Any, input_name: str, field_name: str) -> str:
        """
        Export to vMix input field
        
        Args:
            data: Data to export (string or list)
            input_name: vMix input name
            field_name: vMix field name (e.g. "HomeLogo.Source")
            
        Returns:
            Success message
        """
        if not input_name or not field_name:
            raise ValueError("Both input_name and field_name required for vMix export")
        
        # Convert data to string if needed
        if isinstance(data, list):
            # For lists, just use first item or convert to comma-separated
            data_str = str(data[0]) if len(data) > 0 else ""
        else:
            data_str = str(data)
        
        # Send to vMix
        self.vmix.set_text(input_name, field_name, data_str)
        
        return f"✓ {input_name}.{field_name}"
    
    def _export_to_file(self, data: Any, filepath: str, format: str) -> str:
        """
        Export to file
        
        Args:
            data: Data to export
            filepath: File path to write to
            format: Format type ('text', 'json', 'csv')
            
        Returns:
            Success message
        """
        if not filepath:
            raise ValueError("Filepath required for file export")
        
        # Create parent directory if needed
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'text':
            self._export_text(data, filepath)
        elif format == 'json':
            self._export_json(data, filepath)
        elif format == 'csv':
            self._export_csv(data, filepath)
        else:
            raise ValueError(f"Unknown format: {format}")
        
        return f"✓ {Path(filepath).name}"
    
    def _export_text(self, data: Any, filepath: str):
        """Export as plain text"""
        with open(filepath, 'w', encoding='utf-8') as f:
            if isinstance(data, list):
                # For player/staff lists
                for item in data:
                    if isinstance(item, dict):
                        # Player: number and name
                        if 'number' in item:
                            f.write(f"{item.get('number', '')} {item.get('name', '')}\n")
                        # Staff: role and name
                        elif 'role' in item:
                            f.write(f"{item.get('role', '')}: {item.get('name', '')}\n")
                        else:
                            f.write(f"{item}\n")
                    else:
                        f.write(f"{item}\n")
            else:
                f.write(str(data))
    
    def _export_json(self, data: Any, filepath: str):
        """Export as JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _export_csv(self, data: Any, filepath: str):
        """Export as CSV"""
        import csv
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            if isinstance(data, list) and len(data) > 0:
                if isinstance(data[0], dict):
                    # Write as CSV with headers
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    # Write as single column
                    writer = csv.writer(f)
                    for item in data:
                        writer.writerow([item])
            else:
                # Write single value
                writer = csv.writer(f)
                writer.writerow([data])
