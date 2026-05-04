#!/bin/bash

# Nombre del archivo de salida
OUTPUT_FILE="status_build.txt"

# Vaciamos el archivo si existe de una ejecución anterior
> "$OUTPUT_FILE"

echo "Iniciando compilación y levantamiento de contenedores..."

# Ejecutamos docker compose. 
# Usamos 'docker compose' (v2), si tienes la v1 muy antigua cambia a 'docker-compose'.
# 2>&1 redirige los errores (stderr) a la salida estándar (stdout) para poder capturar todo junto.
# Ejecutamos en detached mode (-d) para que el script termine una vez levantados.
OUTPUT=$(docker compose up --build -d 2>&1)

# Guardamos el código de salida del comando anterior (0 = Éxito, distinto de 0 = Error)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    # Si todo salió bien, escribimos el mensaje de éxito
    echo "compilacion_ok" > "$OUTPUT_FILE"
    echo "✅ Proceso completado con éxito. Revisa $OUTPUT_FILE."
else
    # Si hubo un error, escribimos el mensaje de error y el detalle completo
    echo "compilacion_error" > "$OUTPUT_FILE"
    echo "================ DETALLE DEL ERROR ================" >> "$OUTPUT_FILE"
    echo "$OUTPUT" >> "$OUTPUT_FILE"
    echo "❌ Ocurrió un error. Revisa el detalle en $OUTPUT_FILE."
fi