import os

print("🎨 APLICANDO MEJORAS DE UX Y GITOPS AL FRONTEND...")

def patch_file(path, search_text, replace_text):
    if not os.path.exists(path):
        print(f"⚠️ Archivo no encontrado: {path}")
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if search_text in content:
        new_content = content.replace(search_text, replace_text)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ Parche aplicado en: {path}")
    else:
        print(f"ℹ️ El texto ya está parcheado o no se encontró en: {path}")

# ==========================================
# 1. PARCHE: URL AUTO-GENERADA (ProjectForm.tsx)
# ==========================================
form_path = "frontend/features/projects/ProjectForm.tsx"

# Inyectar la lógica de generación de Slug/GitHub URL
handle_change_logic = """
  function set<K extends keyof ProyectoCreate>(key: K, value: ProyectoCreate[K]) {
    setPayload((prev) => ({ ...prev, [key]: value }));
  }

  const handleTituloChange = (val: string) => {
    set("titulo", val);
    const slug = val.toLowerCase().trim().replace(/ /g, '-').replace(/[^\\w-]+/g, '');
    set("github_url", `https://github.com/LTVitoto/${slug}.git`);
  };
"""

# Reemplazar la función set vieja por la nueva lógica
patch_file(
    form_path,
    "  function set<K extends keyof ProyectoCreate>(key: K, value: ProyectoCreate[K]) {\n    setPayload((prev) => ({ ...prev, [key]: value }));\n  }",
    handle_change_logic
)

# Reemplazar el onChange del input del título
patch_file(
    form_path,
    'value={payload.titulo} onChange={(e) => set("titulo", e.target.value)}',
    'value={payload.titulo} onChange={(e) => handleTituloChange(e.target.value)}'
)

# ==========================================
# 2. PARCHE: ESTADO GITHUB (ConfigView.tsx)
# ==========================================
config_path = "frontend/features/config/ConfigView.tsx"

github_badge_ui = """
            {[
              ["OpenAI", config?.has_api_key_openai, config?.saldo_virtual_openai],
              ["Anthropic", config?.has_api_key_anthropic, config?.saldo_virtual_anthropic],
              ["Gemini", config?.has_api_key_gemini, config?.saldo_virtual_gemini]
            ].map(([name, hasKey, saldo]) => (
              <div key={String(name)} className="rounded-3xl border border-brand-border bg-white p-5">
                <div className="text-lg font-black">{String(name)}</div>
                <Badge tone={hasKey ? "success" : "neutral"} className="mt-3">{hasKey ? "Key cargada" : "Sin key"}</Badge>
                <p className="mt-5 text-sm text-brand-muted">Saldo virtual</p>
                <p className="text-2xl font-black text-brand-navy">{Number(saldo || 0).toFixed(4)}</p>
              </div>
            ))}
            <div className="rounded-3xl border border-brand-border bg-white p-5">
              <div className="text-lg font-black">GitHub GitOps</div>
              <Badge tone={(config as any)?.has_api_key_github ? "success" : "danger"} className="mt-3">
                {(config as any)?.has_api_key_github ? "Token Cargado" : "Falta Token"}
              </Badge>
              <p className="mt-5 text-sm text-brand-muted">Auto-Despliegue</p>
              <p className="text-xs font-bold text-brand-cyan uppercase tracking-wider">Habilitado</p>
            </div>
"""

# Reemplazar el bloque de mapeo de llaves para incluir GitHub
patch_file(
    config_path,
    """            {[
              ["OpenAI", config?.has_api_key_openai, config?.saldo_virtual_openai],
              ["Anthropic", config?.has_api_key_anthropic, config?.saldo_virtual_anthropic],
              ["Gemini", config?.has_api_key_gemini, config?.saldo_virtual_gemini]
            ].map(([name, hasKey, saldo]) => (
              <div key={String(name)} className="rounded-3xl border border-brand-border bg-white p-5">
                <div className="text-lg font-black">{String(name)}</div>
                <Badge tone={hasKey ? "success" : "neutral"} className="mt-3">{hasKey ? "Key cargada" : "Sin key"}</Badge>
                <p className="mt-5 text-sm text-brand-muted">Saldo virtual</p>
                <p className="text-2xl font-black text-brand-navy">{Number(saldo || 0).toFixed(4)}</p>
              </div>
            ))}""",
    github_badge_ui
)

print("\n🚀 FRONTEND ACTUALIZADO. Next.js recargará los cambios automáticamente.")