import json
from pathlib import Path
from services.parser.router import parse_portfolio

fixtures_dir = Path('tests/fixtures/portfolios')
for f in sorted(fixtures_dir.glob('*.pdf')):
    print('='*60)
    print(f.name)
    print('='*60)
    try:
        result = parse_portfolio(str(f))
        print(f'  Skills: {len(result.skills)}  Experience: {len(result.experience)}  Projects: {len(result.projects)}  Certs: {len(result.certifications)}')
        print(f'  Warnings: {len(result.warnings)}')
        for w in result.warnings:
            print(f'    [{w.severity}] {w.message}')
        print(f'  Uncategorized keys: {list(result.uncategorized.keys())}')
    except Exception as e:
        print(f'  FAILED: {e}')
    print()