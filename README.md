# Data-Lake-Architecture

<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-4479A1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>


[Portugues](#portugues) | [English](#english)

---

## Portugues

### Descricao

Implementacao de arquitetura de Data Lake em Python com zonas de armazenamento (raw/processed/curated), catalogo de metadados SQLite e dashboard Flask para gerenciamento de assets.

### O que este projeto faz

- Armazenamento de dados em multiplas zonas (raw, bronze, silver, gold) no sistema de arquivos local
- Catalogo de metadados com SQLite para registro, busca e tagueamento de assets
- Ingestao de dados com checksums SHA-256 para integridade de arquivos
- Busca e tagueamento de assets de dados
- Dashboard web Flask para navegacao, busca e ingestao de dados
- Geracao de dados de exemplo (clientes e transacoes)
- Suporte a formatos Parquet, CSV e JSON
- Rastreamento de linhagem de dados entre assets

### O que este projeto NAO possui

- Processamento paralelo ou distribuido
- Validacao de schema
- Alertas ou monitoramento
- Configuracao via YAML/JSON
- Containerizacao (Docker)
- CI/CD
- Testes abrangentes (apenas scaffold)

### Tecnologias

| Tecnologia | Descricao | Papel |
|------------|-----------|-------|
| **Python** | Linguagem principal | Core |
| **Flask** | Framework web leve | Dashboard web |
| **pandas** | Biblioteca de manipulacao de dados | Leitura/escrita de dados |
| **SQLite** | Banco de dados embutido | Catalogo de metadados |
| **pyarrow** | Motor Apache Arrow | Suporte a formato Parquet |
| **numpy** | Computacao numerica | Geracao de dados de exemplo |

### Arquitetura

```mermaid
graph TB
    subgraph DataLakeStorage["DataLakeStorage"]
        RAW["Zona Raw"]
        BRONZE["Zona Bronze"]
        SILVER["Zona Silver"]
        GOLD["Zona Gold"]
        CHECKSUM["Checksums SHA-256"]
    end

    subgraph MetadataCatalog["MetadataCatalog"]
        SQLITE["SQLite DB"]
        REGISTER["Registro de Assets"]
        SEARCH["Busca de Assets"]
        TAGS["Tagueamento"]
        LINEAGE["Linhagem de Dados"]
    end

    subgraph DataLakeManager["DataLakeManager"]
        INGEST["Pipeline de Ingestao"]
        TRANSFORM["Transformacao de Dados"]
        SUMMARY["Resumo por Zona"]
    end

    subgraph FlaskDashboard["Flask Dashboard"]
        HOME["/ - Pagina Principal"]
        API_ZONES["/zone_summary"]
        API_ASSETS["/assets"]
        API_SEARCH["/search"]
        API_GENERATE["/generate_sample"]
    end

    DataLakeManager --> DataLakeStorage
    DataLakeManager --> MetadataCatalog
    FlaskDashboard --> DataLakeManager
    INGEST --> RAW
    INGEST --> CHECKSUM
    INGEST --> REGISTER
    SEARCH --> SQLITE
    REGISTER --> SQLITE
```

### Como Executar

```bash
# Clonar o repositorio
git clone https://github.com/galafis/Data-Lake-Architecture.git
cd Data-Lake-Architecture

# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Executar a aplicacao
python data_lake.py
```

O servidor Flask sera iniciado em `http://localhost:5000`.

### Estrutura do Projeto

```
Data-Lake-Architecture/
├── tests/              # Scaffold de testes
│   ├── __init__.py
│   └── test_main.py
├── LICENSE
├── README.md
├── data_lake.py        # Modulo principal (toda a logica)
└── requirements.txt
```

### Testes

O diretorio `tests/` contem apenas um scaffold basico. Nao ha testes unitarios abrangentes implementados.

```bash
pytest tests/ -v
```

---

## English

### Description

Data Lake architecture implementation in Python with storage zones (raw/processed/curated), SQLite metadata catalog, and Flask dashboard for asset management.

### What this project does

- Multi-zone data storage (raw, bronze, silver, gold) on local filesystem
- Metadata catalog with SQLite for asset registration, search, and tagging
- Data ingestion with SHA-256 checksums for file integrity
- Data asset search and tagging
- Flask web dashboard for browsing, searching, and ingesting data
- Sample data generation (customers and transactions)
- Support for Parquet, CSV, and JSON formats
- Data lineage tracking between assets

### What this project does NOT have

- Parallel or distributed processing
- Schema validation
- Alerting or monitoring
- YAML/JSON configuration
- Containerization (Docker)
- CI/CD
- Comprehensive testing (scaffold only)

### Technologies

| Technology | Description | Role |
|------------|-------------|------|
| **Python** | Main language | Core |
| **Flask** | Lightweight web framework | Web dashboard |
| **pandas** | Data manipulation library | Data read/write |
| **SQLite** | Embedded database | Metadata catalog |
| **pyarrow** | Apache Arrow engine | Parquet format support |
| **numpy** | Numerical computing | Sample data generation |

### Architecture

```mermaid
graph TB
    subgraph DataLakeStorage["DataLakeStorage"]
        RAW["Raw Zone"]
        BRONZE["Bronze Zone"]
        SILVER["Silver Zone"]
        GOLD["Gold Zone"]
        CHECKSUM["SHA-256 Checksums"]
    end

    subgraph MetadataCatalog["MetadataCatalog"]
        SQLITE["SQLite DB"]
        REGISTER["Asset Registration"]
        SEARCH["Asset Search"]
        TAGS["Tagging"]
        LINEAGE["Data Lineage"]
    end

    subgraph DataLakeManager["DataLakeManager"]
        INGEST["Ingestion Pipeline"]
        TRANSFORM["Data Transformation"]
        SUMMARY["Zone Summary"]
    end

    subgraph FlaskDashboard["Flask Dashboard"]
        HOME["/ - Main Page"]
        API_ZONES["/zone_summary"]
        API_ASSETS["/assets"]
        API_SEARCH["/search"]
        API_GENERATE["/generate_sample"]
    end

    DataLakeManager --> DataLakeStorage
    DataLakeManager --> MetadataCatalog
    FlaskDashboard --> DataLakeManager
    INGEST --> RAW
    INGEST --> CHECKSUM
    INGEST --> REGISTER
    SEARCH --> SQLITE
    REGISTER --> SQLITE
```

### How to Run

```bash
# Clone the repository
git clone https://github.com/galafis/Data-Lake-Architecture.git
cd Data-Lake-Architecture

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python data_lake.py
```

The Flask server will start at `http://localhost:5000`.

### Project Structure

```
Data-Lake-Architecture/
├── tests/              # Test scaffold
│   ├── __init__.py
│   └── test_main.py
├── LICENSE
├── README.md
├── data_lake.py        # Main module (all logic)
└── requirements.txt
```

### Tests

The `tests/` directory contains only a basic scaffold. There are no comprehensive unit tests implemented.

```bash
pytest tests/ -v
```

### Author

**Gabriel Demetrios Lafis**
- GitHub: [@galafis](https://github.com/galafis)
- LinkedIn: [Gabriel Demetrios Lafis](https://linkedin.com/in/gabriel-demetrios-lafis)

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
