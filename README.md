# TwentyQ - Sistema Inteligente de Adivinanza
Un juego moderno de "20 preguntas" que utiliza árboles de decisión y algoritmos de optimización para adivinar lo que estás pensando.

## 📋 Descripción
**TwentyQ** es una implementación avanzada del clásico juego de las veinte preguntas que combina:
- 🧠 Algoritmos inteligentes de selección de preguntas
- 📊 Base de datos estructurada con múltiples categorías
- 🌳 Árboles de decisión jerárquicos
- ⚡ Optimización basada en teoría de la información

El sistema puede identificar personas, animales, plantas, objetos, lugares y conceptos abstractos mediante preguntas estratégicamente seleccionadas.

## ✨ Características
- **Alta precisión**: Algoritmo optimizado que maximiza la ganancia de información
- **Múltiples categorías**: Más de 25 subcategorías diferentes
- **Flujos especializados**: Routers inteligentes para cada tipo de entidad
- **Manejo de incertidumbre**: Soporte para respuestas "no sé"
- **Interfaz intuitiva**: Interacción simple por consola
- **Modular**: Fácil agregar nuevas categorías

## 🗂️ Estructura de Categorías
### Seres Vivos
- **Animales**: Mamíferos, Aves, Reptiles, Peces, Insectos, Anfibios, Arácnidos, Crustáceos, Moluscos
- **Plantas**: Frutas, Verduras, Flores, Árboles, Hierbas, Cereales, Plantas medicinales, Ornamentales

### Entidades Físicas
- **Objetos**: Hogar, Tecnología, Herramientas, Transporte, Ropa
- **Lugares**: Naturales, Artificiales, Países/Ciudades
- **Alimentos y Bebidas**: Platillos, Ingredientes, Bebidas

### Entidades Abstractas
- **Personas**: Profesiones, Personajes, Roles sociales
- **Conceptos**: Emociones, Valores, Ideas, Eventos
- **Adjetivos**: Colores, Cualitativos, Cuantitativos, Posesivos

## Estructura del Proyecto

```
twentyq/
├── README.md
├── twentyq.py                 # Código principal
├── LICENSE
├── datasets/
│   ├── Personas/
│   │   ├── Profesiones.csv
│   │   ├── Personajes.csv
│   │   └── ...
│   ├── Conceptos/
│   │   ├── Emociones.csv
│   │   ├── Valores.csv
│   │   └── ...
│   └── Adjetivos/
│       ├── Colores.csv
│       └── ...
└── docs/
    └── informe_tecnico.md
```

## Arquitectura Técnica

### Algoritmo Principal
El sistema utiliza la función `pick_next_flag` que implementa:

```python
score = 1.0 - abs(0.5 - p)
```

Donde `p` es la proporción de candidatos que cumplen un atributo. Esto maximiza la ganancia de información seleccionando preguntas que dividen el conjunto lo más equitativamente posible.

### Flujo de Decisión
1. **Árbol General** → Clasificación inicial en categorías amplias
2. **Router Especializado** → Selección de subcategoría específica  
3. **Flujo Optimizado** → Preguntas dirigidas con algoritmo de optimización

## 📊 Datasets

Los datasets fueron creados completamente desde cero debido a la falta de conjuntos de datos existentes que cumplieran con nuestros requerimientos específicos. Cada CSV contiene:

- `nombre`: Identificador único
- `subcategoria`: Clasificación específica
- `atributos_booleanos`: Características para diferenciación
