#!/bin/bash
set -e

echo "🛠️ Ejecutando Auto-Patcher Enterprise para erradicar dependencias circulares en routers..."

cat << 'EOF' > fix_routers.py
import os

routers_dir = 'backend/app/routers'

for filename in os.listdir(routers_dir):
    if not filename.endswith('.py'):
        continue
        
    path = os.path.join(routers_dir, filename)
    with open(path, 'r') as f:
        lines = f.readlines()
    
    models_to_import = []
    out_lines = []
    
    # 1. Extraer y purgar los imports problemáticos de la cabecera
    for line in lines:
        if line.startswith('from app.models import'):
            models = line.replace('from app.models import', '').strip().split(',')
            models_to_import.extend([m.strip() for m in models])
        else:
            out_lines.append(line)
            
    if not models_to_import:
        continue
        
    models_str = ', '.join(set(models_to_import))
    import_stmt = f"    from app.models import {models_str}\n"
    
    final_lines = []
    in_def_params = False
    
    # 2. Inyectar de forma segura en cada función (soportando firmas multilínea de FastAPI)
    for line in out_lines:
        final_lines.append(line)
        clean_line = line.split('#')[0].strip()
        
        if clean_line.startswith('def ') or clean_line.startswith('async def '):
            if clean_line.endswith(':'):
                final_lines.append(import_stmt)
            else:
                in_def_params = True
        elif in_def_params and clean_line.endswith(':'):
            in_def_params = False
            final_lines.append(import_stmt)
            
    with open(path, 'w') as f:
        f.writelines(final_lines)

print("✅ Todos los routers han sido parcheados con Lazy Imports exitosamente.")
EOF

python3 fix_routers.py
rm fix_routers.py

echo "🚀 Reinicia tu contenedor. Uvicorn está blindado."