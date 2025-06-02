#!/usr/bin/env python3
"""
Data Lake Architecture
Modern data lake implementation with metadata management and data governance.
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sqlite3
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from flask import Flask, jsonify, request, render_template_string

@dataclass
class DataAsset:
    """Represents a data asset in the data lake."""
    asset_id: str
    name: str
    path: str
    format: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime
    schema: Dict[str, str]
    tags: List[str]
    owner: str
    description: str
    checksum: str

class DataLakeStorage:
    """Manages data storage in the data lake."""
    
    def __init__(self, base_path: str = "data_lake"):
        self.base_path = Path(base_path)
        self.zones = {
            'raw': self.base_path / 'raw',
            'bronze': self.base_path / 'bronze', 
            'silver': self.base_path / 'silver',
            'gold': self.base_path / 'gold'
        }
        
        # Create zone directories
        for zone_path in self.zones.values():
            zone_path.mkdir(parents=True, exist_ok=True)
    
    def store_data(self, data: pd.DataFrame, zone: str, dataset_name: str, 
                   format: str = 'parquet') -> str:
        """Store data in specified zone."""
        if zone not in self.zones:
            raise ValueError(f"Invalid zone: {zone}")
        
        # Create dataset directory
        dataset_path = self.zones[zone] / dataset_name
        dataset_path.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{dataset_name}_{timestamp}.{format}"
        file_path = dataset_path / filename
        
        # Store data based on format
        if format == 'parquet':
            data.to_parquet(file_path, index=False)
        elif format == 'csv':
            data.to_csv(file_path, index=False)
        elif format == 'json':
            data.to_json(file_path, orient='records')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return str(file_path)
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """Load data from file path."""
        path = Path(file_path)
        
        if path.suffix == '.parquet':
            return pd.read_parquet(file_path)
        elif path.suffix == '.csv':
            return pd.read_csv(file_path)
        elif path.suffix == '.json':
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    def list_datasets(self, zone: str) -> List[str]:
        """List all datasets in a zone."""
        if zone not in self.zones:
            return []
        
        zone_path = self.zones[zone]
        return [d.name for d in zone_path.iterdir() if d.is_dir()]
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get file information."""
        path = Path(file_path)
        if not path.exists():
            return {}
        
        stat = path.stat()
        return {
            'size_bytes': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
            'checksum': self._calculate_checksum(file_path)
        }
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

class MetadataCatalog:
    """Manages metadata catalog for data assets."""
    
    def __init__(self, db_path: str = "metadata_catalog.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize metadata database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_assets (
                asset_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL,
                format TEXT NOT NULL,
                size_bytes INTEGER,
                created_at TEXT,
                updated_at TEXT,
                schema TEXT,
                tags TEXT,
                owner TEXT,
                description TEXT,
                checksum TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lineage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_asset_id TEXT,
                target_asset_id TEXT,
                transformation TEXT,
                created_at TEXT,
                FOREIGN KEY (source_asset_id) REFERENCES data_assets (asset_id),
                FOREIGN KEY (target_asset_id) REFERENCES data_assets (asset_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_asset(self, asset: DataAsset) -> bool:
        """Register a new data asset."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO data_assets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset.asset_id,
                asset.name,
                asset.path,
                asset.format,
                asset.size_bytes,
                asset.created_at.isoformat(),
                asset.updated_at.isoformat(),
                json.dumps(asset.schema),
                json.dumps(asset.tags),
                asset.owner,
                asset.description,
                asset.checksum
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error registering asset: {e}")
            return False
    
    def get_asset(self, asset_id: str) -> Optional[DataAsset]:
        """Get asset by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM data_assets WHERE asset_id = ?", (asset_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return DataAsset(
                asset_id=row[0],
                name=row[1],
                path=row[2],
                format=row[3],
                size_bytes=row[4],
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6]),
                schema=json.loads(row[7]),
                tags=json.loads(row[8]),
                owner=row[9],
                description=row[10],
                checksum=row[11]
            )
        return None
    
    def search_assets(self, query: str = "", tags: List[str] = None) -> List[DataAsset]:
        """Search assets by query and tags."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = "SELECT * FROM data_assets WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (name LIKE ? OR description LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        
        if tags:
            for tag in tags:
                sql += " AND tags LIKE ?"
                params.append(f"%{tag}%")
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        assets = []
        for row in rows:
            assets.append(DataAsset(
                asset_id=row[0],
                name=row[1],
                path=row[2],
                format=row[3],
                size_bytes=row[4],
                created_at=datetime.fromisoformat(row[5]),
                updated_at=datetime.fromisoformat(row[6]),
                schema=json.loads(row[7]),
                tags=json.loads(row[8]),
                owner=row[9],
                description=row[10],
                checksum=row[11]
            ))
        
        return assets
    
    def add_lineage(self, source_id: str, target_id: str, transformation: str):
        """Add data lineage relationship."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO lineage (source_asset_id, target_asset_id, transformation, created_at)
            VALUES (?, ?, ?, ?)
        """, (source_id, target_id, transformation, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

class DataLakeManager:
    """Main data lake management interface."""
    
    def __init__(self, base_path: str = "data_lake"):
        self.storage = DataLakeStorage(base_path)
        self.catalog = MetadataCatalog()
    
    def ingest_data(self, data: pd.DataFrame, name: str, owner: str, 
                   description: str, tags: List[str] = None, zone: str = 'raw') -> str:
        """Ingest data into the data lake."""
        # Store data
        file_path = self.storage.store_data(data, zone, name)
        
        # Get file info
        file_info = self.storage.get_file_info(file_path)
        
        # Create asset
        asset_id = hashlib.md5(f"{name}_{datetime.now()}".encode()).hexdigest()
        asset = DataAsset(
            asset_id=asset_id,
            name=name,
            path=file_path,
            format=Path(file_path).suffix[1:],
            size_bytes=file_info['size_bytes'],
            created_at=file_info['created_at'],
            updated_at=file_info['modified_at'],
            schema={col: str(dtype) for col, dtype in data.dtypes.items()},
            tags=tags or [],
            owner=owner,
            description=description,
            checksum=file_info['checksum']
        )
        
        # Register in catalog
        self.catalog.register_asset(asset)
        
        return asset_id
    
    def transform_data(self, source_asset_id: str, transformation_func, 
                      target_name: str, target_zone: str = 'silver') -> str:
        """Transform data and create new asset."""
        # Get source asset
        source_asset = self.catalog.get_asset(source_asset_id)
        if not source_asset:
            raise ValueError(f"Source asset not found: {source_asset_id}")
        
        # Load source data
        source_data = self.storage.load_data(source_asset.path)
        
        # Apply transformation
        transformed_data = transformation_func(source_data)
        
        # Store transformed data
        target_asset_id = self.ingest_data(
            transformed_data,
            target_name,
            source_asset.owner,
            f"Transformed from {source_asset.name}",
            source_asset.tags + ['transformed'],
            target_zone
        )
        
        # Add lineage
        self.catalog.add_lineage(
            source_asset_id,
            target_asset_id,
            transformation_func.__name__ if hasattr(transformation_func, '__name__') else 'custom_transform'
        )
        
        return target_asset_id
    
    def get_zone_summary(self) -> Dict[str, Any]:
        """Get summary of all zones."""
        summary = {}
        
        for zone_name in self.storage.zones.keys():
            datasets = self.storage.list_datasets(zone_name)
            assets = self.catalog.search_assets()
            zone_assets = [a for a in assets if zone_name in a.path]
            
            total_size = sum(a.size_bytes for a in zone_assets)
            
            summary[zone_name] = {
                'dataset_count': len(datasets),
                'asset_count': len(zone_assets),
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        
        return summary

# Flask Web Interface
app = Flask(__name__)
data_lake = DataLakeManager()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Data Lake Architecture</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .zones { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .zone { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .zone h3 { margin-top: 0; color: #007bff; }
        .assets { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .asset { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        .asset-header { font-weight: bold; color: #333; }
        .asset-meta { color: #666; font-size: 0.9em; margin-top: 5px; }
        .controls { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .search { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ Data Lake Architecture</h1>
            <p>Modern data lake with metadata management and governance</p>
        </div>
        
        <div class="controls">
            <h3>Controls</h3>
            <button onclick="generateSampleData()">Generate Sample Data</button>
            <button onclick="refreshDashboard()">Refresh Dashboard</button>
            <input type="text" id="searchInput" class="search" placeholder="Search assets..." onkeyup="searchAssets()">
        </div>
        
        <div class="zones" id="zonesGrid">
            <!-- Zones will be loaded here -->
        </div>
        
        <div class="assets">
            <h3>Data Assets</h3>
            <div id="assetsList">
                <!-- Assets will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        function generateSampleData() {
            fetch('/generate_sample', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    refreshDashboard();
                });
        }
        
        function refreshDashboard() {
            loadZoneSummary();
            loadAssets();
        }
        
        function loadZoneSummary() {
            fetch('/zone_summary')
                .then(response => response.json())
                .then(data => {
                    const grid = document.getElementById('zonesGrid');
                    grid.innerHTML = '';
                    
                    for (const [zone, summary] of Object.entries(data)) {
                        const zoneDiv = document.createElement('div');
                        zoneDiv.className = 'zone';
                        zoneDiv.innerHTML = `
                            <h3>${zone.toUpperCase()} Zone</h3>
                            <p><strong>Datasets:</strong> ${summary.dataset_count}</p>
                            <p><strong>Assets:</strong> ${summary.asset_count}</p>
                            <p><strong>Size:</strong> ${summary.total_size_mb} MB</p>
                        `;
                        grid.appendChild(zoneDiv);
                    }
                });
        }
        
        function loadAssets() {
            fetch('/assets')
                .then(response => response.json())
                .then(data => {
                    const list = document.getElementById('assetsList');
                    list.innerHTML = '';
                    
                    data.forEach(asset => {
                        const assetDiv = document.createElement('div');
                        assetDiv.className = 'asset';
                        assetDiv.innerHTML = `
                            <div class="asset-header">${asset.name}</div>
                            <div class="asset-meta">
                                Owner: ${asset.owner} | Format: ${asset.format} | 
                                Size: ${(asset.size_bytes / 1024).toFixed(1)} KB |
                                Tags: ${asset.tags.join(', ')}
                            </div>
                            <div style="margin-top: 5px; color: #666;">${asset.description}</div>
                        `;
                        list.appendChild(assetDiv);
                    });
                });
        }
        
        function searchAssets() {
            const query = document.getElementById('searchInput').value;
            fetch(`/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    const list = document.getElementById('assetsList');
                    list.innerHTML = '';
                    
                    data.forEach(asset => {
                        const assetDiv = document.createElement('div');
                        assetDiv.className = 'asset';
                        assetDiv.innerHTML = `
                            <div class="asset-header">${asset.name}</div>
                            <div class="asset-meta">
                                Owner: ${asset.owner} | Format: ${asset.format} | 
                                Size: ${(asset.size_bytes / 1024).toFixed(1)} KB |
                                Tags: ${asset.tags.join(', ')}
                            </div>
                            <div style="margin-top: 5px; color: #666;">${asset.description}</div>
                        `;
                        list.appendChild(assetDiv);
                    });
                });
        }
        
        // Initial load
        refreshDashboard();
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/zone_summary')
def zone_summary():
    """Get zone summary."""
    return jsonify(data_lake.get_zone_summary())

@app.route('/assets')
def get_assets():
    """Get all assets."""
    assets = data_lake.catalog.search_assets()
    return jsonify([asdict(asset) for asset in assets])

@app.route('/search')
def search_assets():
    """Search assets."""
    query = request.args.get('q', '')
    assets = data_lake.catalog.search_assets(query)
    return jsonify([asdict(asset) for asset in assets])

@app.route('/generate_sample', methods=['POST'])
def generate_sample():
    """Generate sample data."""
    try:
        # Generate sample datasets
        
        # Raw data - customer data
        customers = pd.DataFrame({
            'customer_id': range(1, 1001),
            'name': [f'Customer_{i}' for i in range(1, 1001)],
            'email': [f'customer{i}@example.com' for i in range(1, 1001)],
            'age': np.random.randint(18, 80, 1000),
            'city': np.random.choice(['New York', 'London', 'Tokyo', 'Paris'], 1000),
            'signup_date': pd.date_range('2020-01-01', periods=1000, freq='D')
        })
        
        data_lake.ingest_data(
            customers, 
            'customers', 
            'data_team', 
            'Customer master data',
            ['customers', 'raw', 'pii'],
            'raw'
        )
        
        # Raw data - transactions
        transactions = pd.DataFrame({
            'transaction_id': range(1, 5001),
            'customer_id': np.random.randint(1, 1001, 5000),
            'amount': np.random.uniform(10, 1000, 5000),
            'product_category': np.random.choice(['Electronics', 'Clothing', 'Books'], 5000),
            'transaction_date': pd.date_range('2023-01-01', periods=5000, freq='H')
        })
        
        data_lake.ingest_data(
            transactions,
            'transactions',
            'data_team',
            'Transaction records',
            ['transactions', 'raw', 'financial'],
            'raw'
        )
        
        return jsonify({'message': 'Sample data generated successfully'})
    except Exception as e:
        return jsonify({'message': f'Error generating sample data: {str(e)}'})

def main():
    """Main execution function."""
    print("Data Lake Architecture")
    print("=" * 25)
    
    print("Starting web interface...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()

