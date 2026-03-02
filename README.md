Aquí tienes un **archivo README.md académico, completo y listo para copiar y pegar** para el repositorio **PGPG** de GitHub, con estructura, propósito y un resumen de uso. No contiene datasets (esto se especifica claramente) y está escrito con tono formal y claro:

---

# PGPG

## Descripción

PGPG es un repositorio de código para la **generación de datos musicales y propuesta de nuevas métricas** orientadas a eventos musicales. El proyecto está implementado íntegramente en Python y su propósito principal es crear conjuntos de datos de audio y anotaciones para tareas de modelado, análisis o síntesis musical.

Este repositorio **no incluye datasets** pre‑generados ni contiene archivos de datos musicales de gran tamaño. Los datos se generan por ejecución de los módulos del proyecto.

## Estructura del Repositorio

La organización de carpetas y archivos en la rama principal (`main`) es la siguiente:

```
PGPG/
├── Chord_Dictionaries/
│   └── ...
├── Generators/
│   └── ...
├── Combined/                    (generado tras ejecución del script principal)
├── SingleNotesPerformances/     (generado tras ejecución)
├── ChordEventsPerformances/     (generado tras ejecución)
├── ComplexEventsPerformances/   (generado tras ejecución)
├── config.py
├── main.py
├── tabalturize_data.py
├── requirements.txt
└── .gitignore
```

### Descripción de componentes

* **Chord_Dictionaries/**
  Contiene archivos JSON con distribuciones o diccionarios de acordes que guían la generación de eventos de acordes.

* **Generators/**
  Módulo con clases y funciones que implementan generadores de eventos musicales como notas simples, eventos de acordes y estructuras complejas.

* **main.py**
  Script principal que orquesta la generación de datasets musicales combinados a partir de distintos generadores.

* **config.py**
  Archivo de configuración que define parámetros globales de generación de datos.

* **tabalturize_data.py**
  Utilidad adicional para transformar o tabular resultados de datasets generados.

* **requirements.txt**
  Lista de dependencias Python necesarias para ejecutar el proyecto.

## Uso y Funcionamiento

### Requisitos previos

1. Tener Python 3 instalado en el sistema.
2. Instalar las dependencias definidas en `requirements.txt` mediante:

```
pip install -r requirements.txt
```

### Generación de datos

La generación de datos se realiza ejecutando el script principal `main.py`. Este script combina distintos generadores para producir archivos de audio y anotaciones estructuradas (.wav y .jams).

Estructura básica de ejecución:

1. **Configuración de parámetros**
   Ajustar valores como el número total de archivos a generar (`NUM_FILES`) y las proporciones de cada tipo de generador en el encabezado del script `main.py`.

2. **Ejecución de generadores**
   Al ejecutar `main.py`, se crean tres clases de eventos musicales:

   * **Notas simples**
     Generadas por el módulo `SingleNotesGenerator`.

   * **Eventos de acordes**
     Generados por `ChordEventsGenerator` usando los diccionarios de acordes.

   * **Eventos complejos**
     Combinación de notas y acordes según una configuración específica.

3. **Unificación de dataset**
   Tras sintetizar los audios y anotaciones individuales, el script recopila los archivos en la carpeta `Combined/` para uso posterior.

### Ejemplo de ejecución

Desde la raíz del proyecto, correr:

```
python main.py
```

Esto producirá:

* Carpeta `Combined/audios/` con archivos de audio.
* Carpeta `Combined/jams/` con anotaciones.

El usuario puede ajustar variables como la carpeta de salida, número de eventos, proporciones y rutas de diccionarios en el propio script `main.py` antes de la ejecución.

## Consideraciones

* El proyecto **no incluye datasets pre‑generados** por razones de tamaño y reproducibilidad; los datos deben generarse localmente.
* El uso de `json` para diccionarios de acordes permite modificar o ampliar reglas musicales sin alterar el código.

## Licencia

La licencia del proyecto no está explícita en los archivos visibles. Antes de usar o redistribuir este software en producción, se recomienda verificar la presencia de un archivo de licencia específico o contactar al autor.

---

Si quieres, puedo darte una **versión técnica con ejemplos de salida esperada** o una **documentación de las clases principales del generador** con explicaciones de parámetros. ¿Quieres eso?
