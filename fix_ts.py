import os

print("🛠️ ACTUALIZANDO CONTRATOS DE TYPESCRIPT...")

domain_path = "frontend/types/domain.ts"
if os.path.exists(domain_path):
    with open(domain_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Inyectamos el campo responsable si no existe
    if "responsable?:" not in content:
        content = content.replace("estado: string;", "estado: string;\n  responsable?: string | null;")
        
        with open(domain_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ frontend/types/domain.ts actualizado con el campo 'responsable'.")
    else:
        print("✅ El campo ya existía en domain.ts")

# Forzamos una re-escritura del formulario para que Next.js (Fast Refresh) lo detecte
form_path = "frontend/features/projects/ProjectForm.tsx"
if os.path.exists(form_path):
    with open(form_path, "a", encoding="utf-8") as f:
        f.write("\n// Force Recompile")
    print("✅ Formulario tocado para forzar recompilación.")

print("🚀 LISTO. Ve a tu navegador, la página se actualizará sola (o dale F5) y verás el campo Responsable.")